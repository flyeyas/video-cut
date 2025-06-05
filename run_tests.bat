@echo off
echo Creating test data directories...
if not exist test_data\videos mkdir test_data\videos
if not exist test_data\audio mkdir test_data\audio

echo Running tests...
cd src
python -m unittest test_video_audio_sync.py
cd ..

echo Tests completed.
pause 