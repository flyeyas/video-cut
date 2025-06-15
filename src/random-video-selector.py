#!/usr/bin/env python3
import os
import sys
import json
import random
import shutil
import subprocess
import argparse
from pathlib import Path
from datetime import datetime

class VideoSelector:
    def __init__(self, source_dir, target_dir, target_duration, 
                 allowed_formats=None, max_error_ratio=0.05):
        self.source_dir = Path(source_dir).resolve()
        self.target_dir = Path(target_dir).resolve()
        self.target_duration = target_duration  # 目标时长(秒)
        self.max_error = target_duration * max_error_ratio
        self.min_acceptable = target_duration - self.max_error
        self.max_acceptable = target_duration + self.max_error
        self.allowed_formats = allowed_formats or []
        self.cache_file = self.source_dir / '.video_duration_cache.json'
        self.video_cache = {}
        self.error_log = []

    def load_cache(self):
        """加载视频时长缓存"""
        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                self.error_log.append(f"加载缓存失败: {str(e)}, 将重新生成缓存")
        return {}

    def save_cache(self):
        """保存视频时长缓存"""
        try:
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.video_cache, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.error_log.append(f"保存缓存失败: {str(e)}")

    def get_video_duration(self, video_path):
        """使用ffprobe获取视频时长(秒)"""
        try:
            result = subprocess.run(
                ['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
                 '-of', 'default=noprint_wrappers=1:nokey=1', str(video_path)],
                capture_output=True, text=True, check=True
            )
            return float(result.stdout.strip())
        except Exception as e:
            self.error_log.append(f"无法读取视频时长: {str(video_path)}, 错误: {str(e)}")
            return 0

    def scan_videos(self):
        """扫描目录中的视频文件并获取时长"""
        # 加载现有缓存
        cached_data = self.load_cache()
        self.video_cache = {'files': {}, 'last_scan': datetime.now().isoformat()}

        # 扫描视频文件
        video_extensions = {'.mp4', '.mov', '.avi', '.mkv', '.flv', '.wmv', '.mpeg', '.mpg'}
        if self.allowed_formats:
            video_extensions = {f'.{ext.lower()}' for ext in self.allowed_formats}

        for root, _, files in os.walk(self.source_dir):
            for file in files:
                ext = Path(file).suffix.lower()
                if ext in video_extensions:
                    video_path = Path(root) / file
                    rel_path = str(video_path.relative_to(self.source_dir))
                    file_mtime = os.path.getmtime(video_path)

                    # 检查缓存是否有效
                    if rel_path in cached_data.get('files', {}) and \
                       cached_data['files'][rel_path].get('mtime', 0) == file_mtime:
                        # 使用缓存数据
                        self.video_cache['files'][rel_path] = cached_data['files'][rel_path]
                    else:
                        # 获取新时长并缓存
                        duration = self.get_video_duration(video_path)
                        if duration > 0:
                            self.video_cache['files'][rel_path] = {
                                'path': str(video_path),
                                'duration': duration,
                                'mtime': file_mtime
                            }

        # 保存更新后的缓存
        self.save_cache()

        # 返回有效的视频文件列表
        return [v for v in self.video_cache['files'].values() if v['duration'] > 0]

    def select_videos(self, videos):
        """随机选择视频直到达到目标时长范围"""
        if not videos:
            return []

        # 打乱视频顺序
        shuffled_videos = random.sample(videos, len(videos))
        selected = []
        total_duration = 0

        for video in shuffled_videos:
            selected.append(video)
            total_duration += video['duration']

            # 检查是否达到目标范围
            if total_duration >= self.min_acceptable:
                break

        # 如果仍未达到最小可接受时长，继续添加（即使超过最大限制）
        if total_duration < self.min_acceptable:
            self.error_log.append(f"警告: 所有可用视频总时长({total_duration}秒)仍小于目标时长的95%({self.min_acceptable}秒)")

        return selected

    def copy_videos(self, selected_videos):
        """复制选中的视频到目标目录，保留目录结构"""
        for video in selected_videos:
            src_path = Path(video['path'])
            rel_path = src_path.relative_to(self.source_dir)
            dest_path = self.target_dir / rel_path

            # 创建目标目录
            dest_path.parent.mkdir(parents=True, exist_ok=True)

            # 如果文件已存在则跳过
            if dest_path.exists():
                self.error_log.append(f"文件已存在，跳过: {str(dest_path)}")
                continue

            # 复制文件
            try:
                shutil.copy2(src_path, dest_path)
                print(f"已复制: {str(rel_path)}")
            except Exception as e:
                self.error_log.append(f"复制失败: {str(rel_path)}, 错误: {str(e)}")

    def run(self):
        """执行视频选择和复制流程"""
        print(f"开始扫描视频文件: {self.source_dir}")
        videos = self.scan_videos()

        if not videos:
            print("未找到有效的视频文件")
            return

        print(f"找到{len(videos)}个有效视频文件")
        print(f"目标时长: {self.target_duration}秒 (可接受范围: {self.min_acceptable:.1f}-{self.max_acceptable:.1f}秒)")

        selected = self.select_videos(videos)
        total_selected = sum(v['duration'] for v in selected)

        print(f"已选择{len(selected)}个视频，总时长: {total_selected:.1f}秒")
        print(f"正在复制到目标目录: {self.target_dir}")

        self.copy_videos(selected)

        # 输出错误日志
        if self.error_log:
            print("\n操作过程中出现以下问题:")
            for error in self.error_log:
                print(f"- {error}")

        print("\n操作完成")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='根据时长随机选择视频素材并复制到目标目录')
    parser.add_argument('-s', '--source', required=True, help='源视频文件夹路径')
    parser.add_argument('-t', '--target', required=True, help='目标目录路径')
    parser.add_argument('-d', '--duration', type=int, required=True, help='目标总时长(秒)')
    parser.add_argument('-f', '--formats', nargs='*', help='允许的视频格式(不带点，如mp4 mov)')
    parser.add_argument('-e', '--error', type=float, default=0.05, help='最大误差比例(默认0.05即5%)')

    args = parser.parse_args()

    selector = VideoSelector(
        source_dir=args.source,
        target_dir=args.target,
        target_duration=args.duration,
        allowed_formats=args.formats,
        max_error_ratio=args.error
    )
    selector.run()