#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
测试 video_analyzer.py 的日志功能
"""

import sys
import os
import tempfile
from pathlib import Path

# 添加 src 目录到路径
sys.path.insert(0, 'src')

from video_analyzer import VideoAnalyzer, set_debug_logging

def test_logging():
    """测试日志功能"""
    print("=== 测试 VideoAnalyzer 日志功能 ===")
    
    # 启用调试日志
    set_debug_logging()
    
    # 创建临时数据库
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_db:
        db_path = tmp_db.name
    
    try:
        # 初始化分析器（这会触发数据库初始化日志）
        print("\n1. 初始化 VideoAnalyzer...")
        analyzer = VideoAnalyzer(db_path=db_path)
        
        # 测试扫描不存在的目录（这会触发错误日志）
        print("\n2. 测试扫描不存在的目录...")
        try:
            analyzer.scan_video_library("/不存在的目录")
        except FileNotFoundError as e:
            print(f"预期的错误: {e}")
        
        # 测试扫描空目录
        print("\n3. 测试扫描空目录...")
        with tempfile.TemporaryDirectory() as tmp_dir:
            count = analyzer.scan_video_library(tmp_dir)
            print(f"扫描结果: {count} 个视频")
        
        print("\n4. 测试查找相似视频（无效ID）...")
        similar_videos = analyzer.find_similar_videos(999)
        print(f"相似视频数量: {len(similar_videos)}")
        
        print("\n=== 日志测试完成 ===")
        print("请检查以下文件中的日志输出:")
        print("- 控制台输出（上面显示的内容）")
        print("- video_analyzer.log 文件")
        
    finally:
        # 清理临时文件
        if os.path.exists(db_path):
            os.unlink(db_path)

if __name__ == "__main__":
    test_logging()
