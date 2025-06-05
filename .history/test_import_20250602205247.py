#!/usr/bin/env python3
# -*- coding: utf-8 -*-

try:
    print("开始测试导入...")
    
    # 测试基础moviepy导入
    import moviepy
    print("✓ moviepy 基础模块导入成功")
    
    # 测试editor模块
    from moviepy import editor
    print("✓ moviepy.editor 模块导入成功")
    
    # 测试具体类
    from moviepy.editor import VideoFileClip
    print("✓ VideoFileClip 导入成功")
    
    from moviepy.editor import AudioFileClip
    print("✓ AudioFileClip 导入成功")
    
    from moviepy.editor import concatenate_videoclips
    print("✓ concatenate_videoclips 导入成功")
    
    print("所有导入测试通过！")
    
except ImportError as e:
    print(f"导入错误: {e}")
    import traceback
    traceback.print_exc()
except Exception as e:
    print(f"其他错误: {e}")
    import traceback
    traceback.print_exc()