import os
import argparse
import shutil
from moviepy.editor import VideoFileClip

def get_video_info(video_path):
    """
    获取视频的信息，包括宽高比
    """
    try:
        clip = VideoFileClip(video_path)
        width, height = clip.size
        ratio = width / height
        duration = clip.duration
        clip.close()
        return {
            'path': video_path,
            'width': width,
            'height': height,
            'ratio': ratio,
            'duration': duration
        }
    except Exception as e:
        print(f"获取视频信息出错: {video_path}, 错误: {e}")
        return None

def classify_ratio(ratio):
    """
    根据宽高比对视频进行分类
    """
    if ratio < 0.5:  # 竖屏窄视频 (例如 9:16)
        return "vertical_narrow"
    elif 0.5 <= ratio < 0.7:  # 竖屏视频 (例如 3:4)
        return "vertical"
    elif 0.7 <= ratio < 1.2:  # 接近正方形的视频
        return "square"
    elif 1.2 <= ratio < 1.5:  # 横屏视频 (例如 4:3)
        return "horizontal"
    elif 1.5 <= ratio < 1.9:  # 宽屏视频 (例如 16:9)
        return "widescreen"
    else:  # 超宽视频
        return "ultrawide"

def get_ratio_folder_name(ratio):
    """
    获取更具描述性的文件夹名称
    """
    category = classify_ratio(ratio)
    if category == "vertical_narrow":
        return "竖屏窄视频_9-16"
    elif category == "vertical":
        return "竖屏视频_3-4"
    elif category == "square":
        return "方形视频_1-1"
    elif category == "horizontal":
        return "横屏视频_4-3"
    elif category == "widescreen":
        return "宽屏视频_16-9"
    else:
        return "超宽视频_21-9"

def get_custom_ratio_folder(ratio, custom_ranges):
    """
    根据自定义的比例范围获取文件夹名称
    """
    for folder_name, (min_ratio, max_ratio) in custom_ranges.items():
        if min_ratio <= ratio < max_ratio:
            return folder_name
    return f"其他比例_{ratio:.2f}"

def sort_videos_by_ratio(input_folder, output_folder, custom_ranges=None, copy_mode=False, extensions=None):
    """
    根据视频比例将视频分类到不同文件夹
    
    参数:
    - input_folder: 输入视频文件夹路径
    - output_folder: 输出根文件夹路径
    - custom_ranges: 自定义比例范围，格式为 {文件夹名: (最小比例, 最大比例)}
    - copy_mode: 如果为True，复制文件而不是移动
    - extensions: 视频文件扩展名列表
    """
    if extensions is None:
        extensions = ['.mp4', '.avi', '.mov', '.flv', '.mkv', '.wmv']
    
    # 确保输出文件夹存在
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)
    
    # 统计信息
    total_videos = 0
    processed_videos = 0
    ratio_counts = {}
    
    # 处理视频文件
    for root, _, files in os.walk(input_folder):
        for file in files:
            if any(file.lower().endswith(ext) for ext in extensions):
                total_videos += 1
                file_path = os.path.join(root, file)
                
                # 获取视频信息
                video_info = get_video_info(file_path)
                if video_info:
                    ratio = video_info['ratio']
                    
                    # 确定目标文件夹
                    if custom_ranges:
                        ratio_folder = get_custom_ratio_folder(ratio, custom_ranges)
                    else:
                        ratio_folder = get_ratio_folder_name(ratio)
                    
                    # 更新统计信息
                    ratio_counts[ratio_folder] = ratio_counts.get(ratio_folder, 0) + 1
                    
                    # 创建目标文件夹
                    target_folder = os.path.join(output_folder, ratio_folder)
                    if not os.path.exists(target_folder):
                        os.makedirs(target_folder)
                    
                    # 目标文件路径
                    target_path = os.path.join(target_folder, file)
                    
                    # 复制或移动文件
                    try:
                        if copy_mode:
                            shutil.copy2(file_path, target_path)
                            print(f"已复制: {file} -> {ratio_folder}/")
                        else:
                            shutil.move(file_path, target_path)
                            print(f"已移动: {file} -> {ratio_folder}/")
                        processed_videos += 1
                    except Exception as e:
                        print(f"处理文件出错: {file}, 错误: {e}")
    
    # 打印统计信息
    print(f"\n处理完成! 共处理 {processed_videos}/{total_videos} 个视频文件")
    print("\n各比例类别统计:")
    for folder, count in ratio_counts.items():
        print(f"  {folder}: {count} 个视频")

def main():
    parser = argparse.ArgumentParser(description='根据视频宽高比将视频分类到不同文件夹')
    parser.add_argument('--input', '-i', required=True, help='输入视频文件夹路径')
    parser.add_argument('--output', '-o', required=True, help='输出根文件夹路径')
    parser.add_argument('--copy', '-c', action='store_true', help='复制文件而不是移动')
    parser.add_argument('--custom', '-r', action='store_true', help='使用自定义比例范围')
    
    args = parser.parse_args()
    
    # 自定义比例范围示例
    custom_ranges = None
    if args.custom:
        custom_ranges = {
            "竖屏视频_9-16": (0.5, 0.65),
            "竖屏视频_3-4": (0.65, 0.85),
            "方形视频_1-1": (0.85, 1.15),
            "横屏视频_4-3": (1.15, 1.4),
            "宽屏视频_16-9": (1.4, 1.9),
            "超宽视频_21-9": (1.9, 3.0)
        }
    
    print(f"开始处理视频文件...")
    print(f"输入文件夹: {args.input}")
    print(f"输出文件夹: {args.output}")
    print(f"模式: {'复制' if args.copy else '移动'}")
    print(f"比例范围: {'自定义' if args.custom else '默认'}")
    
    sort_videos_by_ratio(args.input, args.output, custom_ranges, args.copy)

if __name__ == "__main__":
    main()