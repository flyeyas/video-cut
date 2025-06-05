import os
import random
import argparse
import glob
from moviepy.editor import VideoFileClip, concatenate_videoclips, AudioFileClip

def get_video_duration(video_path):
    """
    获取视频的时长
    """
    try:
        clip = VideoFileClip(video_path)
        duration = clip.duration
        clip.close()
        return duration
    except Exception as e:
        print(f"获取视频时长出错: {video_path}, 错误: {e}")
        return None

def get_all_video_clips(folder_path, extensions=None):
    """
    获取文件夹中所有视频文件的路径和时长信息
    """
    if extensions is None:
        extensions = ['.mp4', '.avi', '.mov', '.flv', '.mkv', '.wmv']
    
    video_info = []
    for root, _, files in os.walk(folder_path):
        for file in files:
            if any(file.lower().endswith(ext) for ext in extensions):
                file_path = os.path.join(root, file)
                duration = get_video_duration(file_path)
                if duration is not None:
                    video_info.append({
                        'path': file_path,
                        'duration': duration
                    })
    
    return video_info

def get_scene_clips(folder_path, extensions=None):
    """
    获取已经分割好的场景片段
    """
    if extensions is None:
        extensions = ['.mp4', '.avi', '.mov', '.flv', '.mkv', '.wmv']
    
    scene_clips = []
    for root, _, files in os.walk(folder_path):
        for file in files:
            if any(file.lower().endswith(ext) for ext in extensions):
                file_path = os.path.join(root, file)
                duration = get_video_duration(file_path)
                if duration is not None:
                    scene_clips.append({
                        'path': file_path,
                        'duration': duration
                    })
    
    return scene_clips

def clip_long_video(video_path, target_duration, max_clip_duration=None):
    """
    从长视频中随机裁剪一段指定时长的片段
    
    参数:
    - video_path: 视频文件路径
    - target_duration: 目标时长（秒）
    - max_clip_duration: 最大裁剪时长，如果为None则使用target_duration
    
    返回:
    - 裁剪后的视频片段对象，如果失败则返回None
    """
    try:
        video = VideoFileClip(video_path)
        video_duration = video.duration
        
        # 如果视频时长小于目标时长，直接返回整个视频
        if video_duration <= target_duration:
            return video
        
        # 确定实际裁剪时长
        clip_duration = min(target_duration, max_clip_duration or target_duration)
        
        # 计算可能的起始时间范围
        max_start_time = video_duration - clip_duration
        
        # 随机选择起始时间
        start_time = random.uniform(0, max_start_time)
        
        # 裁剪视频
        clipped_video = video.subclip(start_time, start_time + clip_duration)
        
        # 关闭原始视频
        video.close()
        
        return clipped_video
    except Exception as e:
        print(f"裁剪视频出错: {video_path}, 错误: {e}")
        return None

def get_audio_duration(audio_path):
    """
    获取音频文件的时长
    """
    try:
        audio = AudioFileClip(audio_path)
        duration = audio.duration
        audio.close()
        return duration
    except Exception as e:
        print(f"获取音频时长出错: {audio_path}, 错误: {e}")
        return None

def find_audio_files(folder_path):
    """
    在指定文件夹中查找音频文件
    """
    audio_extensions = ['.mp3', '.wav', '.aac', '.flac', '.ogg', '.m4a']
    audio_files = []
    
    for ext in audio_extensions:
        audio_files.extend(glob.glob(os.path.join(folder_path, f"*{ext}")))
        # 递归搜索子文件夹
        audio_files.extend(glob.glob(os.path.join(folder_path, f"**/*{ext}"), recursive=True))
    
    return audio_files

def auto_determine_clip_duration(clips):
    """
    根据视频库中的视频时长自动确定最佳的最大裁剪时长
    """
    if not clips:
        return 30  # 默认值
    
    # 计算所有视频时长的中位数
    durations = [clip['duration'] for clip in clips]
    durations.sort()
    median_duration = durations[len(durations) // 2]
    
    # 将中位数作为参考，但不超过60秒
    return min(median_duration, 60)

def random_select_clips(clips, target_duration, max_attempts=100, auto_clip=True, max_clip_duration=None):
    """
    随机选择视频片段，使总时长接近目标时长
    
    参数:
    - clips: 视频片段列表
    - target_duration: 目标时长（秒）
    - max_attempts: 最大尝试次数
    - auto_clip: 是否自动裁剪长视频
    - max_clip_duration: 自动裁剪时的最大片段时长（秒）
    """
    if not clips:
        return []
    
    selected_clips = []
    current_duration = 0
    attempts = 0
    
    # 如果未指定最大裁剪时长，自动确定一个合适的值
    if max_clip_duration is None:
        max_clip_duration = auto_determine_clip_duration(clips)
        print(f"自动设置最大裁剪时长为: {max_clip_duration:.2f}秒")
    
    # 按时长排序，方便后续选择
    sorted_clips = sorted(clips, key=lambda x: x['duration'])
    
    while current_duration < target_duration and attempts < max_attempts:
        # 计算还需要的时长
        remaining_duration = target_duration - current_duration
        
        # 找出所有时长小于等于剩余时长的片段
        suitable_clips = [clip for clip in clips if clip['duration'] <= remaining_duration]
        
        if not suitable_clips:
            if auto_clip:
                # 如果启用了自动裁剪，尝试从较长的视频中裁剪
                longer_clips = [clip for clip in clips if clip['duration'] > remaining_duration]
                
                if longer_clips:
                    # 随机选择一个较长的视频
                    long_clip = random.choice(longer_clips)
                    
                    # 添加裁剪信息
                    clip_info = {
                        'path': long_clip['path'],
                        'duration': min(remaining_duration, max_clip_duration),
                        'needs_clipping': True,
                        'start_time': random.uniform(0, long_clip['duration'] - min(remaining_duration, max_clip_duration))
                    }
                    
                    selected_clips.append(clip_info)
                    current_duration += clip_info['duration']
                else:
                    # 如果没有更长的视频可供裁剪，就结束循环
                    break
            else:
                # 如果没有启用自动裁剪，尝试找最短的一个
                if sorted_clips and sorted_clips[0]['duration'] + current_duration <= target_duration * 1.1:
                    clip = sorted_clips[0]
                    selected_clips.append(clip)
                    current_duration += clip['duration']
                else:
                    # 如果最短的也太长，就结束循环
                    break
        else:
            # 随机选择一个合适的片段
            clip = random.choice(suitable_clips)
            selected_clips.append(clip)
            current_duration += clip['duration']
        
        attempts += 1
    
    return selected_clips

def combine_video_clips(selected_clips, output_path):
    """
    将选中的视频片段合并成一个视频
    """
    if not selected_clips:
        print("没有选中任何视频片段")
        return False
    
    try:
        video_clips = []
        
        for clip_info in selected_clips:
            if clip_info.get('needs_clipping', False):
                # 需要裁剪的视频
                video = VideoFileClip(clip_info['path'])
                clipped_video = video.subclip(clip_info['start_time'], 
                                             clip_info['start_time'] + clip_info['duration'])
                video_clips.append(clipped_video)
                # 原始视频在处理完后关闭
                video.close()
            else:
                # 不需要裁剪的视频
                video_clips.append(VideoFileClip(clip_info['path']))
        
        final_clip = concatenate_videoclips(video_clips)
        final_clip.write_videofile(output_path, codec='libx264', audio_codec='aac')
        
        # 关闭所有视频片段
        for clip in video_clips:
            clip.close()
        final_clip.close()
        
        return True
    except Exception as e:
        print(f"合并视频出错: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(description='根据目标时长从视频库中随机选择并组合视频片段')
    parser.add_argument('--input', '-i', required=True, help='输入视频文件夹路径')
    parser.add_argument('--output', '-o', required=True, help='输出视频文件路径')
    parser.add_argument('--duration', '-d', type=float, help='目标视频时长（秒），如不指定则自动从音频文件获取')
    parser.add_argument('--audio', '-a', help='音频文件路径，用于自动确定目标时长')
    parser.add_argument('--audio_folder', '-af', help='音频文件夹路径，将随机选择一个音频文件确定目标时长')
    parser.add_argument('--scene_folder', '-s', help='已分割场景的文件夹路径，如果提供则优先使用场景片段')
    parser.add_argument('--max_clip_duration', '-m', type=float, help='自动裁剪时的最大片段时长（秒），不指定则自动确定')
    
    args = parser.parse_args()
    
    # 确定目标时长
    target_duration = None
    
    # 如果直接指定了时长，使用指定的时长
    if args.duration:
        target_duration = args.duration
    # 如果指定了音频文件，从音频文件获取时长
    elif args.audio and os.path.exists(args.audio):
        target_duration = get_audio_duration(args.audio)
        if target_duration:
            print(f"从音频文件获取目标时长: {target_duration:.2f}秒")
    # 如果指定了音频文件夹，随机选择一个音频文件获取时长
    elif args.audio_folder and os.path.exists(args.audio_folder):
        audio_files = find_audio_files(args.audio_folder)
        if audio_files:
            selected_audio = random.choice(audio_files)
            target_duration = get_audio_duration(selected_audio)
            if target_duration:
                print(f"从随机选择的音频文件 {os.path.basename(selected_audio)} 获取目标时长: {target_duration:.2f}秒")
    
    # 如果无法确定目标时长，使用默认值
    if not target_duration:
        target_duration = 60.0  # 默认1分钟
        print(f"无法确定目标时长，使用默认值: {target_duration}秒")
    
    # 获取视频片段
    if args.scene_folder and os.path.exists(args.scene_folder):
        print(f"使用已分割的场景片段: {args.scene_folder}")
        clips = get_scene_clips(args.scene_folder)
    else:
        print(f"从视频库获取片段: {args.input}")
        clips = get_all_video_clips(args.input)
    
    if not clips:
        print("未找到任何视频片段")
        return
    
    print(f"找到 {len(clips)} 个视频片段")
    
    # 随机选择视频片段（始终启用自动裁剪功能）
    selected_clips = random_select_clips(
        clips, 
        target_duration, 
        auto_clip=True, 
        max_clip_duration=args.max_clip_duration
    )
    
    if not selected_clips:
        print("无法选择合适的视频片段组合")
        return
    
    total_duration = sum(clip['duration'] for clip in selected_clips)
    print(f"已选择 {len(selected_clips)} 个视频片段，总时长: {total_duration:.2f}秒")
    
    # 输出裁剪信息
    clipped_count = sum(1 for clip in selected_clips if clip.get('needs_clipping', False))
    if clipped_count > 0:
        print(f"其中 {clipped_count} 个视频片段需要自动裁剪")
    
    # 合并视频片段
    success = combine_video_clips(selected_clips, args.output)
    
    if success:
        print(f"视频已成功生成: {args.output}")
    else:
        print("视频生成失败")

if __name__ == "__main__":
    main()