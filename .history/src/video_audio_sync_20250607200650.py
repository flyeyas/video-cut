#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import logging
import argparse
from pathlib import Path
from typing import Dict, Any

from video_analyzer import VideoAnalyzer, set_debug_logging
from video_composer import VideoComposer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('video_audio_sync')

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Video Audio Sync - Create videos synchronized with audio",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    # Common arguments
    parser.add_argument("--db-path", default="video_library.db",
                        help="Path to the database file")
    parser.add_argument("--debug", action="store_true",
                        help="Enable debug logging")
    
    # Create subparsers for different commands
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # Analyzer command
    analyzer_parser = subparsers.add_parser("analyze", help="Analyze video library")
    analyzer_parser.add_argument("--video-dir", required=True,
                               help="Directory containing video files")
    
    # Composer command
    composer_parser = subparsers.add_parser("compose", help="Compose video from segments")
    composer_parser.add_argument("--audio", required=False,
                               help="Path to the audio file (optional)")
    composer_parser.add_argument("--duration", type=float, required=False,
                               help="Duration of the output video in seconds (required if audio not provided)")
    composer_parser.add_argument("--output", required=True,
                               help="Path to save the output video")
    composer_parser.add_argument("--similarity-threshold", type=float, default=0.5,
                               help="Similarity threshold for video selection (0-1)")
    composer_parser.add_argument("--min-segment", type=float, default=1.0,
                               help="Minimum segment duration in seconds")
    composer_parser.add_argument("--max-segment", type=float, default=10.0,
                               help="Maximum segment duration in seconds")
    composer_parser.add_argument("--export-draft", action="store_true",
                               help="Export CapCut/JianYing draft files")
    composer_parser.add_argument("--draft-dir", default="./drafts",
                               help="Directory to save draft files")
    
    # Full pipeline command
    pipeline_parser = subparsers.add_parser("pipeline", help="Run full pipeline (analyze + compose)")
    pipeline_parser.add_argument("--video-dir", required=True,
                               help="Directory containing video files")
    pipeline_parser.add_argument("--audio", required=False,
                               help="Path to the audio file (optional)")
    pipeline_parser.add_argument("--duration", type=float, required=False,
                               help="Duration of the output video in seconds (required if audio not provided)")
    pipeline_parser.add_argument("--output", required=True,
                               help="Path to save the output video")
    pipeline_parser.add_argument("--similarity-threshold", type=float, default=0.5,
                               help="Similarity threshold for video selection (0-1)")
    pipeline_parser.add_argument("--min-segment", type=float, default=1.0,
                               help="Minimum segment duration in seconds")
    pipeline_parser.add_argument("--max-segment", type=float, default=10.0,
                               help="Maximum segment duration in seconds")
    pipeline_parser.add_argument("--export-draft", action="store_true",
                               help="Export CapCut/JianYing draft files")
    pipeline_parser.add_argument("--draft-dir", default="./drafts",
                               help="Directory to save draft files")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # 检查composer和pipeline命令是否同时缺少audio和duration参数
    if args.command in ["compose", "pipeline"] and not args.audio and args.duration is None:
        if args.command == "compose":
            composer_parser.error("必须提供--audio或--duration参数之一")
        else:
            pipeline_parser.error("必须提供--audio或--duration参数之一")
        
    return args

def run_analyzer(args):
    """Run the video analyzer module."""
    logger.info(f"Analyzing video library at {args.video_dir}")
    analyzer = VideoAnalyzer(db_path=args.db_path)
    count = analyzer.scan_video_library(args.video_dir)
    logger.info(f"Processed {count} videos")
    return count

def run_composer(args):
    """Run the video composer module."""
    composer = VideoComposer(db_path=args.db_path)
    
    # 确定视频时长
    if args.audio:
        logger.info(f"使用音频文件: {args.audio}")
        audio_metadata = composer.analyze_audio(args.audio)
        video_duration = audio_metadata['duration']
        logger.info(f"音频时长: {video_duration:.2f} 秒")
    else:
        logger.info(f"使用指定时长: {args.duration} 秒")
        video_duration = args.duration
    
    # Select videos
    video_segments = composer.select_videos(
        audio_duration=video_duration,
        similarity_threshold=args.similarity_threshold,
        min_segment_duration=args.min_segment,
        max_segment_duration=args.max_segment
    )
    
    if not video_segments:
        logger.error("没有找到合适的视频片段。请先运行分析器。")
        return None
    
    # Compose video
    output_path = composer.compose_video(
        video_segments=video_segments,
        audio_path=args.audio if args.audio else None,  # 音频可选
        output_path=args.output
    )
    
    # Export draft if requested
    if args.export_draft:
        os.makedirs(args.draft_dir, exist_ok=True)
        draft_dir = composer.export_draft(
            video_segments=video_segments,
            audio_path=args.audio if args.audio else None,  # 音频可选
            output_dir=args.draft_dir
        )
        logger.info(f"CapCut/JianYing草稿已导出到: {draft_dir}")
    
    logger.info(f"视频合成成功: {output_path}")
    return output_path

def run_pipeline(args):
    """Run the full pipeline (analyze + compose)."""
    # First run the analyzer
    count = run_analyzer(args)
    if count == 0:
        logger.error("未找到或处理视频。请检查您的视频目录。")
        return None
    
    # Then run the composer
    output_path = run_composer(args)
    return output_path

def main():
    """Main entry point."""
    args = parse_arguments()
    
    # 设置调试日志级别
    if args.debug:
        set_debug_logging()
        logger.setLevel(logging.DEBUG)
        for handler in logger.handlers:
            handler.setLevel(logging.DEBUG)
        logger.debug("调试模式已启用")
    
    try:
        if args.command == "analyze":
            run_analyzer(args)
        elif args.command == "compose":
            run_composer(args)
        elif args.command == "pipeline":
            run_pipeline(args)
    except Exception as e:
        logger.error(f"错误: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 