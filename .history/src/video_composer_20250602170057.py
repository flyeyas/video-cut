#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import shutil
import tempfile
import logging
import random
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Any, Union

import numpy as np
from moviepy.editor import VideoFileClip, AudioFileClip, concatenate_videoclips
import ffmpeg

from video_analyzer import VideoAnalyzer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('video_composer')

class VideoComposer:
    """Video composition module for selecting, cutting, and composing videos."""
    
    def __init__(self, db_path: str = 'video_library.db'):
        """
        Initialize the VideoComposer with a database path.
        
        Args:
            db_path: Path to the SQLite database file
        """
        self.db_path = db_path
        self.analyzer = VideoAnalyzer(db_path=db_path)
        self.temp_dir = None
    
    def analyze_audio(self, audio_path: str) -> Dict[str, Any]:
        """
        Analyze an audio file to get its duration and other properties.
        
        Args:
            audio_path: Path to the audio file
            
        Returns:
            Dictionary containing audio metadata
        """
        try:
            probe = ffmpeg.probe(audio_path)
            audio_stream = next((stream for stream in probe['streams'] 
                               if stream['codec_type'] == 'audio'), None)
            if audio_stream is None:
                raise ValueError(f"No audio stream found in {audio_path}")
            
            # Extract metadata
            duration = float(probe['format']['duration'])
            sample_rate = int(audio_stream.get('sample_rate', 0))
            channels = int(audio_stream.get('channels', 0))
            
            return {
                'duration': duration,
                'sample_rate': sample_rate,
                'channels': channels,
                'path': audio_path
            }
        except ffmpeg.Error as e:
            logger.error(f"FFmpeg error: {e.stderr}")
            raise
    
    def select_videos(self, 
                     audio_duration: float, 
                     similarity_threshold: float = 0.5,
                     min_segment_duration: float = 1.0,
                     max_segment_duration: float = 10.0) -> List[Dict[str, Any]]:
        """
        Select videos to compose a video of the given duration.
        
        Args:
            audio_duration: Duration of the audio file in seconds
            similarity_threshold: Maximum similarity threshold between videos
            min_segment_duration: Minimum duration of each video segment
            max_segment_duration: Maximum duration of each video segment
            
        Returns:
            List of dictionaries containing video segment information
        """
        # Initialize variables
        total_duration = 0
        selected_segments = []
        
        # Get random dissimilar videos
        # We request more videos than we might need
        estimated_segments = int(audio_duration / min_segment_duration) * 2
        candidate_videos = self.analyzer.get_random_dissimilar_videos(
            count=estimated_segments, 
            similarity_threshold=similarity_threshold
        )
        
        if not candidate_videos:
            raise ValueError("No videos found in the database. Run the video analyzer first.")
        
        # Shuffle videos for randomness
        random.shuffle(candidate_videos)
        
        # Select videos until we reach the target duration
        while total_duration < audio_duration and candidate_videos:
            video = candidate_videos.pop(0)
            video_duration = video['duration']
            
            # Skip videos that are too short
            if video_duration < min_segment_duration:
                continue
                
            # Determine segment duration
            remaining_duration = audio_duration - total_duration
            
            if video_duration <= remaining_duration:
                # Use the entire video if it fits in the remaining duration
                segment_duration = min(video_duration, max_segment_duration)
            else:
                # Use a portion of the video
                segment_duration = min(remaining_duration, max_segment_duration)
            
            # Select a random start point that ensures we have enough video
            max_start = max(0, video_duration - segment_duration)
            start_time = random.uniform(0, max_start) if max_start > 0 else 0
            
            # Add segment to the list
            segment = {
                'video_id': video['id'],
                'file_path': video['file_path'],
                'start_time': start_time,
                'duration': segment_duration,
                'resolution': video['resolution']
            }
            selected_segments.append(segment)
            total_duration += segment_duration
            
            # If we're close enough to the target duration, stop
            if audio_duration - total_duration < min_segment_duration:
                break
        
        # Adjust the last segment if needed to match the audio duration exactly
        if selected_segments and total_duration > audio_duration:
            last_segment = selected_segments[-1]
            duration_diff = total_duration - audio_duration
            last_segment['duration'] -= duration_diff
        
        logger.info(f"Selected {len(selected_segments)} video segments for a {audio_duration:.2f}s composition")
        return selected_segments
    
    def cut_video(self, video_path: str, start_time: float, duration: float, output_path: str) -> str:
        """
        Cut a video segment from a video file.
        
        Args:
            video_path: Path to the video file
            start_time: Start time in seconds
            duration: Duration in seconds
            output_path: Path to save the cut video
            
        Returns:
            Path to the cut video
        """
        try:
            # Ensure output directory exists
            os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
            
            # Cut the video using ffmpeg
            (
                ffmpeg
                .input(video_path, ss=start_time, t=duration)
                .output(output_path, c='copy')
                .run(quiet=True, overwrite_output=True)
            )
            
            logger.debug(f"Cut video segment: {start_time:.2f}s to {start_time+duration:.2f}s from {video_path}")
            return output_path
        except ffmpeg.Error as e:
            logger.error(f"FFmpeg error while cutting video: {e.stderr}")
            
            # Fallback to slower but more reliable method using moviepy
            logger.info(f"Falling back to MoviePy for cutting video: {video_path}")
            try:
                with VideoFileClip(video_path) as clip:
                    subclip = clip.subclip(start_time, start_time + duration)
                    subclip.write_videofile(output_path, codec='libx264', audio=False)
                return output_path
            except Exception as e2:
                logger.error(f"MoviePy error: {e2}")
                raise
    
    def compose_video(self, 
                     video_segments: List[Dict[str, Any]], 
                     audio_path: str, 
                     output_path: str,
                     target_resolution: Tuple[int, int] = (1920, 1080)) -> str:
        """
        Compose a video from segments with the given audio.
        
        Args:
            video_segments: List of dictionaries containing video segment information
            audio_path: Path to the audio file
            output_path: Path to save the composed video
            target_resolution: Target resolution as (width, height)
            
        Returns:
            Path to the composed video
        """
        # Create a temporary directory for cut segments
        self.temp_dir = tempfile.mkdtemp()
        cut_segments = []
        
        try:
            # Cut each segment
            for i, segment in enumerate(video_segments):
                segment_path = os.path.join(self.temp_dir, f"segment_{i:03d}.mp4")
                self.cut_video(
                    segment['file_path'], 
                    segment['start_time'], 
                    segment['duration'], 
                    segment_path
                )
                cut_segments.append(segment_path)
            
            # Compose the video using MoviePy
            clips = []
            for segment_path in cut_segments:
                clip = VideoFileClip(segment_path)
                # Resize to target resolution
                clip = clip.resize(target_resolution)
                clips.append(clip)
            
            # Concatenate video clips
            final_clip = concatenate_videoclips(clips)
            
            # Add audio
            audio_clip = AudioFileClip(audio_path)
            final_clip = final_clip.set_audio(audio_clip)
            
            # Write the final video
            final_clip.write_videofile(
                output_path, 
                codec='libx264', 
                audio_codec='aac', 
                fps=30
            )
            
            # Close clips
            final_clip.close()
            audio_clip.close()
            for clip in clips:
                clip.close()
                
            logger.info(f"Composed video saved to {output_path}")
            return output_path
            
        finally:
            # Clean up temporary files
            if self.temp_dir and os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir)
                self.temp_dir = None
    
    def export_draft(self, 
                    video_segments: List[Dict[str, Any]], 
                    audio_path: str, 
                    output_dir: str) -> str:
        """
        Export a CapCut/JianYing draft file.
        
        Args:
            video_segments: List of dictionaries containing video segment information
            audio_path: Path to the audio file
            output_dir: Directory to save the draft files
            
        Returns:
            Path to the draft directory
        """
        # Create draft directory
        draft_dir = os.path.join(output_dir, "draft_project")
        os.makedirs(draft_dir, exist_ok=True)
        
        # Generate draft_content.json
        draft_content = self._generate_draft_content(video_segments, audio_path)
        
        # Generate draft_meta_info.json
        draft_meta = self._generate_draft_meta_info()
        
        # Write files
        with open(os.path.join(draft_dir, "draft_content.json"), 'w', encoding='utf-8') as f:
            json.dump(draft_content, f, ensure_ascii=False, indent=2)
            
        with open(os.path.join(draft_dir, "draft_meta_info.json"), 'w', encoding='utf-8') as f:
            json.dump(draft_meta, f, ensure_ascii=False, indent=2)
            
        logger.info(f"CapCut/JianYing draft exported to {draft_dir}")
        return draft_dir
    
    def _generate_draft_content(self, video_segments: List[Dict[str, Any]], audio_path: str) -> Dict:
        """Generate the draft_content.json structure for CapCut/JianYing."""
        # Calculate total duration in microseconds (CapCut uses microseconds)
        total_duration_us = int(sum(segment['duration'] for segment in video_segments) * 1000000)
        
        # Generate materials section
        materials = {
            "videos": [],
            "audios": []
        }
        
        # Add videos
        for i, segment in enumerate(video_segments):
            video_id = f"video_{i}"
            materials["videos"].append({
                "id": video_id,
                "path": segment['file_path'],
                "name": os.path.basename(segment['file_path']),
                "duration": int(segment['duration'] * 1000000)  # Convert to microseconds
            })
        
        # Add audio
        audio_id = "audio_0"
        audio_duration = int(sum(segment['duration'] for segment in video_segments) * 1000000)
        materials["audios"].append({
            "id": audio_id,
            "path": audio_path,
            "name": os.path.basename(audio_path),
            "duration": audio_duration
        })
        
        # Generate tracks section
        tracks = []
        
        # Video track
        video_segments_data = []
        current_time = 0
        
        for i, segment in enumerate(video_segments):
            video_id = f"video_{i}"
            duration_us = int(segment['duration'] * 1000000)
            
            video_segments_data.append({
                "id": f"video_segment_{i}",
                "material_id": video_id,
                "start_time": current_time,
                "duration": duration_us,
                "material_start_time": int(segment['start_time'] * 1000000),
                "speed": 1.0
            })
            
            current_time += duration_us
        
        tracks.append({
            "type": "video",
            "segments": video_segments_data
        })
        
        # Audio track
        tracks.append({
            "type": "audio",
            "segments": [{
                "id": "audio_segment_0",
                "material_id": audio_id,
                "start_time": 0,
                "duration": audio_duration,
                "material_start_time": 0,
                "volume": 1.0
            }]
        })
        
        # Final draft content structure
        draft_content = {
            "version": "5.9",  # CapCut/JianYing version
            "materials": materials,
            "tracks": tracks,
            "canvas": {
                "width": 1920,
                "height": 1080,
                "duration": total_duration_us
            }
        }
        
        return draft_content
    
    def _generate_draft_meta_info(self) -> Dict:
        """Generate the draft_meta_info.json structure for CapCut/JianYing."""
        return {
            "version": "5.9",
            "id": f"draft_{int(time.time())}",
            "name": f"Auto Generated Draft {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            "duration": 0,  # Will be filled by CapCut/JianYing
            "cover_image": "",
            "created_at": int(time.time()),
            "modified_at": int(time.time())
        }

if __name__ == "__main__":
    import argparse
    import time
    from datetime import datetime
    
    parser = argparse.ArgumentParser(description="Video composer")
    parser.add_argument("--audio", required=True, help="Path to the audio file")
    parser.add_argument("--output", required=True, help="Path to save the output video")
    parser.add_argument("--db-path", default="video_library.db", help="Path to the database file")
    parser.add_argument("--similarity-threshold", type=float, default=0.5, 
                        help="Similarity threshold for video selection (0-1)")
    parser.add_argument("--min-segment", type=float, default=1.0, 
                        help="Minimum segment duration in seconds")
    parser.add_argument("--max-segment", type=float, default=10.0, 
                        help="Maximum segment duration in seconds")
    parser.add_argument("--export-draft", action="store_true", 
                        help="Export CapCut/JianYing draft files")
    parser.add_argument("--draft-dir", default="./drafts", 
                        help="Directory to save draft files")
    
    args = parser.parse_args()
    
    composer = VideoComposer(db_path=args.db_path)
    
    # Analyze audio
    audio_metadata = composer.analyze_audio(args.audio)
    audio_duration = audio_metadata['duration']
    
    # Select videos
    video_segments = composer.select_videos(
        audio_duration=audio_duration,
        similarity_threshold=args.similarity_threshold,
        min_segment_duration=args.min_segment,
        max_segment_duration=args.max_segment
    )
    
    # Compose video
    output_path = composer.compose_video(
        video_segments=video_segments,
        audio_path=args.audio,
        output_path=args.output
    )
    
    # Export draft if requested
    if args.export_draft:
        os.makedirs(args.draft_dir, exist_ok=True)
        draft_dir = composer.export_draft(
            video_segments=video_segments,
            audio_path=args.audio,
            output_dir=args.draft_dir
        )
        print(f"CapCut/JianYing draft exported to: {draft_dir}")
    
    print(f"Video composed successfully: {output_path}") 