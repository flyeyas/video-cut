#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import time
import sqlite3
import hashlib
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Tuple, Optional, Any

import cv2
import numpy as np
import ffmpeg

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('video_analyzer')

# Define supported video formats
SUPPORTED_VIDEO_FORMATS = ['.mp4', '.mov', '.avi', '.mkv', '.wmv', '.flv']

class VideoAnalyzer:
    """Video analysis module for scanning and extracting features from video files."""
    
    def __init__(self, db_path: str = 'video_library.db'):
        """
        Initialize the VideoAnalyzer with a database path.
        
        Args:
            db_path: Path to the SQLite database file
        """
        self.db_path = db_path
        self._init_database()
        self.current_feature_version = "v1.0"  # Update this when feature extraction algorithm changes
        
    def _init_database(self):
        """Initialize the SQLite database with required tables."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create video_metadata table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS video_metadata (
            id INTEGER PRIMARY KEY,
            file_path TEXT UNIQUE,
            duration REAL,
            resolution TEXT,
            file_size INTEGER,
            last_modified TIMESTAMP,
            feature_version TEXT,
            analyzed_at TIMESTAMP
        )
        ''')
        
        # Create video_features table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS video_features (
            video_id INTEGER,
            feature_type TEXT,
            feature_data BLOB,
            PRIMARY KEY (video_id, feature_type),
            FOREIGN KEY (video_id) REFERENCES video_metadata(id)
        )
        ''')
        
        # Create feature_versions table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS feature_versions (
            version TEXT PRIMARY KEY,
            algorithm TEXT,
            parameters TEXT,
            created_at TIMESTAMP
        )
        ''')
        
        # Insert current feature version if not exists
        cursor.execute('''
        INSERT OR IGNORE INTO feature_versions (version, algorithm, parameters, created_at)
        VALUES (?, ?, ?, ?)
        ''', (self.current_feature_version, "phash+colorhist", "default", datetime.now()))
        
        conn.commit()
        conn.close()
        
    def scan_video_library(self, directory_path: str) -> int:
        """
        Scan a directory for video files and extract features.
        
        Args:
            directory_path: Path to the directory containing video files
            
        Returns:
            Number of videos processed
        """
        logger.info(f"Scanning video library at {directory_path}")
        directory = Path(directory_path)
        if not directory.exists():
            raise FileNotFoundError(f"Directory not found: {directory_path}")
        
        count = 0
        for file_path in self._find_video_files(directory):
            try:
                self._process_video_file(file_path)
                count += 1
            except Exception as e:
                logger.error(f"Error processing {file_path}: {e}")
                
        logger.info(f"Processed {count} videos in {directory_path}")
        return count
    
    def _find_video_files(self, directory: Path) -> List[Path]:
        """Find all video files in a directory recursively."""
        video_files = []
        for file_path in directory.rglob('*'):
            if file_path.is_file() and file_path.suffix.lower() in SUPPORTED_VIDEO_FORMATS:
                video_files.append(file_path)
        return video_files
    
    def _process_video_file(self, file_path: Path) -> int:
        """
        Process a single video file: extract metadata and features.
        
        Args:
            file_path: Path to the video file
            
        Returns:
            video_id: The ID of the video in the database
        """
        str_path = str(file_path.absolute())
        file_stats = file_path.stat()
        last_modified = datetime.fromtimestamp(file_stats.st_mtime)
        file_size = file_stats.st_size
        
        # Check if video is already in the database and needs update
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, last_modified, feature_version FROM video_metadata WHERE file_path = ?", 
            (str_path,)
        )
        result = cursor.fetchone()
        
        if result:
            video_id, db_last_modified, db_feature_version = result
            db_last_modified = datetime.fromisoformat(db_last_modified)
            
            # If file hasn't changed and feature version is current, skip processing
            if (last_modified == db_last_modified and 
                db_feature_version == self.current_feature_version):
                conn.close()
                logger.debug(f"Skipping unchanged file: {file_path.name}")
                return video_id
            
            # Update existing record
            logger.info(f"Updating video metadata and features: {file_path.name}")
        else:
            # New video file
            logger.info(f"Processing new video file: {file_path.name}")
            video_id = None
        
        # Extract metadata
        try:
            metadata = self._extract_video_metadata(str_path)
        except Exception as e:
            logger.error(f"Failed to extract metadata from {file_path.name}: {e}")
            conn.close()
            raise
        
        # Update or insert metadata
        if video_id:
            cursor.execute('''
            UPDATE video_metadata 
            SET duration = ?, resolution = ?, file_size = ?, 
                last_modified = ?, feature_version = ?, analyzed_at = ?
            WHERE id = ?
            ''', (
                metadata['duration'], metadata['resolution'], file_size,
                last_modified.isoformat(), self.current_feature_version, 
                datetime.now().isoformat(), video_id
            ))
        else:
            cursor.execute('''
            INSERT INTO video_metadata 
            (file_path, duration, resolution, file_size, last_modified, feature_version, analyzed_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                str_path, metadata['duration'], metadata['resolution'], file_size,
                last_modified.isoformat(), self.current_feature_version, 
                datetime.now().isoformat()
            ))
            video_id = cursor.lastrowid
        
        # Extract features
        try:
            features = self._extract_video_features(str_path)
            
            # Delete existing features if any
            cursor.execute("DELETE FROM video_features WHERE video_id = ?", (video_id,))
            
            # Insert new features
            for feature_type, feature_data in features.items():
                cursor.execute('''
                INSERT INTO video_features (video_id, feature_type, feature_data)
                VALUES (?, ?, ?)
                ''', (video_id, feature_type, feature_data))
                
        except Exception as e:
            logger.error(f"Failed to extract features from {file_path.name}: {e}")
            # Continue with metadata only if feature extraction fails
        
        conn.commit()
        conn.close()
        return video_id
    
    def _extract_video_metadata(self, file_path: str) -> Dict[str, Any]:
        """
        Extract metadata from a video file using ffmpeg.
        
        Args:
            file_path: Path to the video file
            
        Returns:
            Dictionary containing video metadata
        """
        try:
            probe = ffmpeg.probe(file_path)
            video_stream = next((stream for stream in probe['streams'] 
                                if stream['codec_type'] == 'video'), None)
            if video_stream is None:
                raise ValueError(f"No video stream found in {file_path}")
            
            # Extract metadata
            duration = float(probe['format']['duration'])
            width = int(video_stream['width'])
            height = int(video_stream['height'])
            resolution = f"{width}x{height}"
            
            return {
                'duration': duration,
                'resolution': resolution,
                'width': width,
                'height': height
            }
        except ffmpeg.Error as e:
            logger.error(f"FFmpeg error: {e.stderr}")
            raise
    
    def _extract_video_features(self, file_path: str) -> Dict[str, bytes]:
        """
        Extract features from a video file.
        
        Args:
            file_path: Path to the video file
            
        Returns:
            Dictionary mapping feature types to feature data
        """
        features = {}
        
        # Extract perceptual hash features
        phash_features = self._extract_phash_features(file_path)
        features['phash'] = self._serialize_feature(phash_features)
        
        # Extract color histogram features
        color_hist_features = self._extract_color_histogram_features(file_path)
        features['colorhist'] = self._serialize_feature(color_hist_features)
        
        return features
    
    def _extract_phash_features(self, file_path: str, sample_rate: int = 1) -> np.ndarray:
        """
        Extract perceptual hash features from video frames.
        
        Args:
            file_path: Path to the video file
            sample_rate: Sample one frame every N seconds
            
        Returns:
            Array of perceptual hash values
        """
        cap = cv2.VideoCapture(file_path)
        if not cap.isOpened():
            raise ValueError(f"Could not open video file: {file_path}")
        
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_interval = int(fps * sample_rate)
        
        phash_list = []
        frame_count = 0
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
                
            if frame_count % frame_interval == 0:
                # Convert to grayscale and resize
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                resized = cv2.resize(gray, (32, 32))
                
                # Compute DCT
                dct = cv2.dct(np.float32(resized))
                dct_low = dct[:8, :8]
                
                # Compute mean
                mean = np.mean(dct_low)
                
                # Compute hash
                hash_value = 0
                for i in range(8):
                    for j in range(8):
                        if dct_low[i, j] > mean:
                            hash_value |= 1 << (i * 8 + j)
                
                phash_list.append(hash_value)
                
            frame_count += 1
            
        cap.release()
        return np.array(phash_list, dtype=np.uint64)
    
    def _extract_color_histogram_features(self, file_path: str, sample_rate: int = 1) -> np.ndarray:
        """
        Extract color histogram features from video frames.
        
        Args:
            file_path: Path to the video file
            sample_rate: Sample one frame every N seconds
            
        Returns:
            Array of color histograms
        """
        cap = cv2.VideoCapture(file_path)
        if not cap.isOpened():
            raise ValueError(f"Could not open video file: {file_path}")
        
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_interval = int(fps * sample_rate)
        
        hist_list = []
        frame_count = 0
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
                
            if frame_count % frame_interval == 0:
                # Convert to HSV
                hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
                
                # Compute histogram
                hist = cv2.calcHist([hsv], [0, 1], None, [8, 8], [0, 180, 0, 256])
                hist = cv2.normalize(hist, hist).flatten()
                
                hist_list.append(hist)
                
            frame_count += 1
            
        cap.release()
        return np.array(hist_list, dtype=np.float32)
    
    def _serialize_feature(self, feature: np.ndarray) -> bytes:
        """Serialize a numpy array to bytes."""
        return feature.tobytes()
    
    def _deserialize_feature(self, data: bytes, dtype) -> np.ndarray:
        """Deserialize bytes to a numpy array."""
        return np.frombuffer(data, dtype=dtype)
    
    def get_video_metadata(self, video_id: int) -> Dict[str, Any]:
        """
        Get metadata for a video.
        
        Args:
            video_id: ID of the video in the database
            
        Returns:
            Dictionary containing video metadata
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT file_path, duration, resolution, file_size, last_modified
        FROM video_metadata
        WHERE id = ?
        ''', (video_id,))
        
        result = cursor.fetchone()
        conn.close()
        
        if not result:
            raise ValueError(f"No video found with ID {video_id}")
        
        file_path, duration, resolution, file_size, last_modified = result
        return {
            'id': video_id,
            'file_path': file_path,
            'duration': duration,
            'resolution': resolution,
            'file_size': file_size,
            'last_modified': last_modified
        }
    
    def get_video_feature(self, video_id: int, feature_type: str) -> np.ndarray:
        """
        Get features for a video.
        
        Args:
            video_id: ID of the video in the database
            feature_type: Type of feature to retrieve ('phash' or 'colorhist')
            
        Returns:
            Numpy array containing feature data
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT feature_data
        FROM video_features
        WHERE video_id = ? AND feature_type = ?
        ''', (video_id, feature_type))
        
        result = cursor.fetchone()
        conn.close()
        
        if not result:
            raise ValueError(f"No {feature_type} feature found for video ID {video_id}")
        
        feature_data = result[0]
        
        # Deserialize based on feature type
        if feature_type == 'phash':
            return self._deserialize_feature(feature_data, np.uint64)
        elif feature_type == 'colorhist':
            return self._deserialize_feature(feature_data, np.float32)
        else:
            raise ValueError(f"Unknown feature type: {feature_type}")
    
    def find_similar_videos(self, video_id: int, threshold: float = 0.8) -> List[Tuple[int, float]]:
        """
        Find videos similar to the given video.
        
        Args:
            video_id: ID of the reference video
            threshold: Similarity threshold (0-1)
            
        Returns:
            List of tuples (video_id, similarity_score)
        """
        # Get features of the reference video
        try:
            ref_phash = self.get_video_feature(video_id, 'phash')
            ref_colorhist = self.get_video_feature(video_id, 'colorhist')
        except ValueError:
            logger.error(f"Could not retrieve features for video ID {video_id}")
            return []
        
        # Get all video IDs
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM video_metadata")
        video_ids = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        similar_videos = []
        for vid in video_ids:
            if vid == video_id:
                continue
                
            try:
                # Get features of the comparison video
                comp_phash = self.get_video_feature(vid, 'phash')
                comp_colorhist = self.get_video_feature(vid, 'colorhist')
                
                # Calculate similarity scores
                phash_sim = self._calculate_phash_similarity(ref_phash, comp_phash)
                colorhist_sim = self._calculate_histogram_similarity(ref_colorhist, comp_colorhist)
                
                # Combine scores (weighted average)
                combined_sim = 0.7 * phash_sim + 0.3 * colorhist_sim
                
                if combined_sim >= threshold:
                    similar_videos.append((vid, combined_sim))
            except ValueError:
                continue
        
        # Sort by similarity (highest first)
        similar_videos.sort(key=lambda x: x[1], reverse=True)
        return similar_videos
    
    def _calculate_phash_similarity(self, phash1: np.ndarray, phash2: np.ndarray) -> float:
        """Calculate similarity between two sets of perceptual hashes."""
        # If arrays have different lengths, use the shorter one
        min_len = min(len(phash1), len(phash2))
        if min_len == 0:
            return 0.0
            
        phash1 = phash1[:min_len]
        phash2 = phash2[:min_len]
        
        # Calculate Hamming distance
        distances = np.zeros(min_len)
        for i in range(min_len):
            xor = phash1[i] ^ phash2[i]
            # Count bits set to 1 (popcount)
            distances[i] = bin(xor).count('1')
        
        # Convert to similarity (0-1)
        # Maximum distance is 64 bits
        similarities = 1.0 - distances / 64.0
        return float(np.mean(similarities))
    
    def _calculate_histogram_similarity(self, hist1: np.ndarray, hist2: np.ndarray) -> float:
        """Calculate similarity between two sets of color histograms."""
        # If arrays have different lengths, use the shorter one
        min_len = min(len(hist1), len(hist2))
        if min_len == 0:
            return 0.0
            
        hist1 = hist1[:min_len]
        hist2 = hist2[:min_len]
        
        # Calculate histogram intersection
        similarities = np.zeros(min_len)
        for i in range(min_len):
            similarities[i] = cv2.compareHist(
                hist1[i].reshape(8, 8), 
                hist2[i].reshape(8, 8), 
                cv2.HISTCMP_INTERSECT
            )
        
        # Normalize to 0-1
        return float(np.mean(similarities))
    
    def get_random_videos(self, count: int, min_duration: float = 1.0, max_duration: float = float('inf')) -> List[Dict[str, Any]]:
        """
        Get random videos from the database.
        
        Args:
            count: Number of videos to retrieve
            min_duration: Minimum video duration in seconds
            max_duration: Maximum video duration in seconds
            
        Returns:
            List of dictionaries containing video metadata
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
        SELECT id, file_path, duration, resolution
        FROM video_metadata
        WHERE duration >= ? AND duration <= ?
        ORDER BY RANDOM()
        LIMIT ?
        ''', (min_duration, max_duration, count))
        
        results = cursor.fetchall()
        conn.close()
        
        videos = []
        for video_id, file_path, duration, resolution in results:
            videos.append({
                'id': video_id,
                'file_path': file_path,
                'duration': duration,
                'resolution': resolution
            })
            
        return videos
    
    def get_random_dissimilar_videos(self, count: int, similarity_threshold: float = 0.5) -> List[Dict[str, Any]]:
        """
        Get random videos that are not similar to each other.
        
        Args:
            count: Number of videos to retrieve
            similarity_threshold: Maximum similarity threshold between videos
            
        Returns:
            List of dictionaries containing video metadata
        """
        # Get all videos
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM video_metadata ORDER BY RANDOM()")
        all_video_ids = [row[0] for row in cursor.fetchall()]
        conn.close()
        
        if not all_video_ids:
            return []
        
        # Start with a random video
        selected_ids = [all_video_ids[0]]
        remaining_ids = all_video_ids[1:]
        
        # Select videos until we have enough or run out of candidates
        while len(selected_ids) < count and remaining_ids:
            candidate_id = remaining_ids.pop(0)
            
            # Check if candidate is similar to any already selected video
            is_similar = False
            for selected_id in selected_ids:
                similar_videos = self.find_similar_videos(selected_id, threshold=similarity_threshold)
                similar_ids = [vid for vid, _ in similar_videos]
                
                if candidate_id in similar_ids:
                    is_similar = True
                    break
            
            if not is_similar:
                selected_ids.append(candidate_id)
        
        # Get metadata for selected videos
        videos = []
        for video_id in selected_ids:
            try:
                metadata = self.get_video_metadata(video_id)
                videos.append(metadata)
            except ValueError:
                continue
                
        return videos

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Video library analyzer")
    parser.add_argument("--video-dir", required=True, help="Directory containing video files")
    parser.add_argument("--db-path", default="video_library.db", help="Path to the database file")
    
    args = parser.parse_args()
    
    analyzer = VideoAnalyzer(db_path=args.db_path)
    count = analyzer.scan_video_library(args.video_dir)
    
    print(f"Processed {count} videos") 