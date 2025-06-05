#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
示例脚本：演示如何使用视频音频同步剪辑工具
"""

import os
import sys
import time
from pathlib import Path

# 添加父目录到 Python 路径，以便导入模块
current_dir = Path(os.path.dirname(os.path.abspath(__file__)))
parent_dir = current_dir.parent
sys.path.append(str(parent_dir))

from src.video_analyzer import VideoAnalyzer
from src.video_composer import VideoComposer

def main():
    """主函数：演示工具的基本用法"""
    # 设置路径
    video_dir = input("请输入视频库路径: ")
    audio_path = input("请输入音频文件路径: ")
    output_path = input("请输入输出视频路径 [output.mp4]: ") or "output.mp4"
    db_path = "video_library.db"
    
    # 1. 分析视频库
    print("\n===== 步骤 1: 分析视频库 =====")
    analyzer = VideoAnalyzer(db_path=db_path)
    count = analyzer.scan_video_library(video_dir)
    print(f"处理了 {count} 个视频文件")
    
    # 2. 分析音频
    print("\n===== 步骤 2: 分析音频 =====")
    composer = VideoComposer(db_path=db_path)
    audio_metadata = composer.analyze_audio(audio_path)
    audio_duration = audio_metadata['duration']
    print(f"音频时长: {audio_duration:.2f} 秒")
    
    # 3. 选择视频片段
    print("\n===== 步骤 3: 选择视频片段 =====")
    video_segments = composer.select_videos(
        audio_duration=audio_duration,
        similarity_threshold=0.5,
        min_segment_duration=1.0,
        max_segment_duration=10.0
    )
    print(f"选择了 {len(video_segments)} 个视频片段")
    
    # 显示选择的片段
    print("\n选择的视频片段:")
    for i, segment in enumerate(video_segments):
        print(f"片段 {i+1}: {os.path.basename(segment['file_path'])}, "
              f"起始时间: {segment['start_time']:.2f}s, "
              f"时长: {segment['duration']:.2f}s")
    
    # 4. 合成视频
    print("\n===== 步骤 4: 合成视频 =====")
    start_time = time.time()
    output_path = composer.compose_video(
        video_segments=video_segments,
        audio_path=audio_path,
        output_path=output_path
    )
    end_time = time.time()
    print(f"视频合成完成，耗时: {end_time - start_time:.2f} 秒")
    print(f"输出视频: {output_path}")
    
    # 5. 导出剪映草稿（可选）
    export_draft = input("\n是否导出剪映草稿文件? (y/n): ").lower() == 'y'
    if export_draft:
        draft_dir = "./drafts"
        os.makedirs(draft_dir, exist_ok=True)
        
        draft_path = composer.export_draft(
            video_segments=video_segments,
            audio_path=audio_path,
            output_dir=draft_dir
        )
        print(f"剪映草稿已导出到: {draft_path}")
    
    print("\n示例运行完成!")

if __name__ == "__main__":
    main() 