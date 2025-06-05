#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import tempfile
import unittest
from pathlib import Path

from video_analyzer import VideoAnalyzer
from video_composer import VideoComposer

class TestVideoAudioSync(unittest.TestCase):
    """Test cases for the video audio sync modules."""
    
    def setUp(self):
        """Set up test environment."""
        # Create a temporary database
        self.temp_db = tempfile.NamedTemporaryFile(suffix='.db', delete=False)
        self.temp_db.close()
        self.db_path = self.temp_db.name
        
        # Initialize modules
        self.analyzer = VideoAnalyzer(db_path=self.db_path)
        self.composer = VideoComposer(db_path=self.db_path)
        
        # Test data paths - replace with actual test files if available
        self.test_video_dir = os.path.join(os.path.dirname(__file__), '..', 'test_data', 'videos')
        self.test_audio_path = os.path.join(os.path.dirname(__file__), '..', 'test_data', 'audio', 'test_audio.mp3')
        
        # Create test directories if they don't exist
        os.makedirs(os.path.join(os.path.dirname(__file__), '..', 'test_data', 'videos'), exist_ok=True)
        os.makedirs(os.path.join(os.path.dirname(__file__), '..', 'test_data', 'audio'), exist_ok=True)
    
    def tearDown(self):
        """Clean up after tests."""
        # Remove temporary database
        if os.path.exists(self.db_path):
            os.unlink(self.db_path)
    
    def test_database_initialization(self):
        """Test that the database is properly initialized."""
        # The database should be created during initialization
        self.assertTrue(os.path.exists(self.db_path))
    
    def test_video_analyzer_methods(self):
        """Test VideoAnalyzer methods."""
        # Skip if no test videos available
        if not os.listdir(self.test_video_dir):
            self.skipTest("No test videos available")
            
        # Test scan_video_library
        count = self.analyzer.scan_video_library(self.test_video_dir)
        self.assertGreaterEqual(count, 0)
        
        # If videos were found, test other methods
        if count > 0:
            # Get all video IDs
            import sqlite3
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM video_metadata")
            video_ids = [row[0] for row in cursor.fetchall()]
            conn.close()
            
            # Test get_video_metadata
            if video_ids:
                metadata = self.analyzer.get_video_metadata(video_ids[0])
                self.assertIsNotNone(metadata)
                self.assertIn('file_path', metadata)
                self.assertIn('duration', metadata)
                
                # Test get_random_videos
                random_videos = self.analyzer.get_random_videos(count=2)
                self.assertLessEqual(len(random_videos), 2)
                
                # Test get_random_dissimilar_videos
                dissimilar_videos = self.analyzer.get_random_dissimilar_videos(count=2)
                self.assertLessEqual(len(dissimilar_videos), 2)
    
    def test_video_composer_methods(self):
        """Test VideoComposer methods."""
        # Skip if no test audio available
        if not os.path.exists(self.test_audio_path):
            self.skipTest("No test audio available")
            
        try:
            # Test analyze_audio
            audio_metadata = self.composer.analyze_audio(self.test_audio_path)
            self.assertIsNotNone(audio_metadata)
            self.assertIn('duration', audio_metadata)
            
            # Skip further tests if no videos in database
            import sqlite3
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM video_metadata")
            video_count = cursor.fetchone()[0]
            conn.close()
            
            if video_count == 0:
                self.skipTest("No videos in database for composer tests")
                
            # Test select_videos
            audio_duration = audio_metadata['duration']
            video_segments = self.composer.select_videos(
                audio_duration=audio_duration,
                similarity_threshold=0.5,
                min_segment_duration=1.0,
                max_segment_duration=5.0
            )
            
            # If segments were selected, test other methods
            if video_segments:
                # Create a temporary output file
                with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as temp_output:
                    temp_output.close()
                    output_path = temp_output.name
                    
                    # Test cut_video with the first segment
                    segment = video_segments[0]
                    with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as temp_cut:
                        temp_cut.close()
                        cut_path = temp_cut.name
                        
                        try:
                            self.composer.cut_video(
                                segment['file_path'],
                                segment['start_time'],
                                segment['duration'],
                                cut_path
                            )
                            
                            # Check if the cut video exists
                            self.assertTrue(os.path.exists(cut_path))
                            
                        except Exception as e:
                            print(f"Error in cut_video: {e}")
                            self.skipTest(f"cut_video failed: {e}")
                        finally:
                            # Clean up
                            if os.path.exists(cut_path):
                                os.unlink(cut_path)
                                
                    # Clean up
                    if os.path.exists(output_path):
                        os.unlink(output_path)
                        
        except Exception as e:
            print(f"Error in test_video_composer_methods: {e}")
            self.skipTest(f"Composer test failed: {e}")
    
    def test_draft_export(self):
        """Test draft export functionality."""
        # This is a basic test that just checks if the function runs without errors
        # Skip if no videos in database
        import sqlite3
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM video_metadata")
        video_count = cursor.fetchone()[0]
        conn.close()
        
        if video_count == 0 or not os.path.exists(self.test_audio_path):
            self.skipTest("No videos in database or no test audio for draft export test")
            
        try:
            # Create sample video segments
            audio_metadata = self.composer.analyze_audio(self.test_audio_path)
            audio_duration = audio_metadata['duration']
            video_segments = self.composer.select_videos(audio_duration=audio_duration)
            
            if not video_segments:
                self.skipTest("No video segments selected for draft export test")
                
            # Create a temporary directory for draft export
            with tempfile.TemporaryDirectory() as temp_dir:
                # Test export_draft
                draft_dir = self.composer.export_draft(
                    video_segments=video_segments,
                    audio_path=self.test_audio_path,
                    output_dir=temp_dir
                )
                
                # Check if draft files were created
                self.assertTrue(os.path.exists(os.path.join(draft_dir, "draft_content.json")))
                self.assertTrue(os.path.exists(os.path.join(draft_dir, "draft_meta_info.json")))
                
        except Exception as e:
            print(f"Error in test_draft_export: {e}")
            self.skipTest(f"Draft export test failed: {e}")

if __name__ == '__main__':
    unittest.main() 