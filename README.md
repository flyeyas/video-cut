# 视频音频同步剪辑工具

这个工具可以根据给定的音频文件或指定的视频时长，从视频库中随机选择并剪辑多个视频片段，最终组合成符合要求的视频。

## 功能特点

- 自动分析视频库中的所有视频
- 提取视频特征，防止选择内容重复的视频
- 根据音频时长或指定时长智能选择视频片段
- 自动剪辑和拼接视频
- 支持导出剪映/CapCut草稿文件
- 模块化设计，可单独使用分析或剪辑功能

## 系统要求

- Python 3.7+
- FFmpeg
- OpenCV
- 足够的磁盘空间用于视频处理

## 安装

1. 克隆仓库：

```bash
git clone https://github.com/yourusername/video-audio-sync.git
cd video-audio-sync
```

2. 安装依赖：

```bash
pip install -r requirements.txt
```

3. 安装FFmpeg（如果尚未安装）：

- **Windows**：
  下载FFmpeg并添加到系统PATH
  
- **macOS**：
  ```bash
  brew install ffmpeg
  ```
  
- **Linux**：
  ```bash
  sudo apt update
  sudo apt install ffmpeg
  ```

## 使用方法

### 1. 分析视频库

首先，需要分析视频库中的视频并提取特征：

```bash
python src/video_audio_sync.py analyze --video-dir /path/to/videos
```

这将扫描指定目录中的所有视频文件，提取特征并存储在数据库中。

### 2. 合成视频

有两种方式可以创建合成视频：

#### 使用音频文件：
```bash
python src/video_audio_sync.py compose --audio /path/to/audio.mp3 --output output.mp4
```

#### 直接指定视频时长（秒）：
```bash
python src/video_audio_sync.py compose --duration 60.0 --output output.mp4
```

### 3. 完整流程（分析+合成）

一次性完成整个流程：

#### 使用音频文件：
```bash
python src/video_audio_sync.py pipeline --video-dir /path/to/videos --audio /path/to/audio.mp3 --output output.mp4
```

#### 直接指定视频时长：
```bash
python src/video_audio_sync.py pipeline --video-dir /path/to/videos --duration 60.0 --output output.mp4
```

### 4. 导出剪映/CapCut草稿

添加`--export-draft`参数可以导出剪映/CapCut草稿文件：

```bash
python src/video_audio_sync.py compose --audio /path/to/audio.mp3 --output output.mp4 --export-draft --draft-dir ./drafts
```

或

```bash
python src/video_audio_sync.py compose --duration 60.0 --output output.mp4 --export-draft --draft-dir ./drafts
```

### 5. 随机选择视频素材

根据指定时长从源目录随机选择视频素材并复制到目标目录：

```bash
python src/random-video-selector.py -s /path/to/source -t /path/to/target -d 60
```

可选参数：
- `-f`：指定允许的视频格式（如 `-f mp4 mov`）
- `-e`：设置最大误差比例（默认0.05，即5%）

## 命令行参数

### 通用参数

- `--db-path`: 数据库文件路径（默认：video_library.db）

### 分析命令 (analyze)

- `--video-dir`: 视频库目录路径（必需）

### 合成命令 (compose)

- `--audio`: 音频文件路径（与--duration二选一）
- `--duration`: 要生成的视频时长，单位为秒（与--audio二选一）
- `--output`: 输出视频文件路径（必需）
- `--similarity-threshold`: 视频相似度阈值，0-1之间（默认：0.5）
- `--min-segment`: 最小视频片段时长，秒（默认：1.0）
- `--max-segment`: 最大视频片段时长，秒（默认：10.0）
- `--export-draft`: 导出剪映/CapCut草稿文件（可选）
- `--draft-dir`: 草稿文件保存目录（默认：./drafts）

### 完整流程命令 (pipeline)

包含分析和合成命令的所有参数。

## 示例

### 基本用法

```bash
# 分析视频库
python src/video_audio_sync.py analyze --video-dir ~/Videos/collection

# 使用音频创建视频
python src/video_audio_sync.py compose --audio ~/Music/background.mp3 --output ~/Videos/result.mp4

# 使用指定时长创建视频
python src/video_audio_sync.py compose --duration 120.0 --output ~/Videos/result.mp4

# 一次性完成整个流程（使用音频）
python src/video_audio_sync.py pipeline --video-dir ~/Videos/collection --audio ~/Music/background.mp3 --output ~/Videos/result.mp4

# 一次性完成整个流程（使用指定时长）
python src/video_audio_sync.py pipeline --video-dir ~/Videos/collection --duration 120.0 --output ~/Videos/result.mp4
```

### 高级用法

```bash
# 调整视频片段时长
python src/video_audio_sync.py compose --audio ~/Music/background.mp3 --output ~/Videos/result.mp4 --min-segment 2.0 --max-segment 8.0

# 使用指定时长的同时调整片段时长
python src/video_audio_sync.py compose --duration 90.0 --output ~/Videos/result.mp4 --min-segment 3.0 --max-segment 15.0

# 导出剪映草稿
python src/video_audio_sync.py compose --audio ~/Music/background.mp3 --output ~/Videos/result.mp4 --export-draft --draft-dir ~/Documents/drafts

# 使用自定义相似度阈值
python src/video_audio_sync.py compose --audio ~/Music/background.mp3 --output ~/Videos/result.mp4 --similarity-threshold 0.7
```

## 技术细节

本工具使用以下技术：

- **视频特征提取**：使用OpenCV提取视频的感知哈希(pHash)和颜色直方图特征
- **视频剪辑**：使用FFmpeg进行快速剪辑，必要时回退到MoviePy
- **视频合成**：使用MoviePy拼接视频片段并添加音频
- **数据存储**：使用SQLite数据库存储视频元数据和特征

## 故障排除

### 常见问题

1. **"No videos found in the database"**
   - 确保先运行`analyze`命令分析视频库

2. **"FFmpeg error"**
   - 确保FFmpeg正确安装并可在命令行中访问

3. **"Could not open video file"**
   - 检查视频文件是否存在且未损坏
   - 确保视频格式受支持

4. **处理速度慢**
   - 视频分析是一次性操作，后续运行会更快
   - 考虑减小视频库大小或使用更强大的硬件

## 许可证

[MIT License](LICENSE)

## 贡献

欢迎贡献！请提交问题或拉取请求。
