#!/bin/bash

# Create test data directories if they don't exist
mkdir -p test_data/videos
mkdir -p test_data/audio

echo "Running tests..."
cd src
python -m unittest test_video_audio_sync.py
cd ..

echo "Tests completed." 