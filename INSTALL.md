# 安装指南

## 系统要求

- Python 3.7+
- FFmpeg
- 足够的磁盘空间用于视频处理

## 安装步骤

### 1. 安装 Python

如果您尚未安装 Python，请从 [Python 官网](https://www.python.org/downloads/) 下载并安装 Python 3.7 或更高版本。

### 2. 安装 FFmpeg

FFmpeg 是视频处理的核心依赖，需要单独安装。

#### Windows

1. 从 [FFmpeg 官网](https://ffmpeg.org/download.html) 或 [gyan.dev](https://www.gyan.dev/ffmpeg/builds/) 下载 FFmpeg
2. 解压到一个目录，例如 `C:\ffmpeg`
3. 将 FFmpeg 的 bin 目录添加到系统 PATH 环境变量中（例如 `C:\ffmpeg\bin`）
4. 打开新的命令提示符，输入 `ffmpeg -version` 验证安装是否成功

#### macOS

使用 Homebrew 安装：

```bash
brew install ffmpeg
```

#### Linux (Ubuntu/Debian)

```bash
sudo apt update
sudo apt install ffmpeg
```

### 3. 克隆或下载项目

```bash
git clone https://github.com/yourusername/video-audio-sync.git
cd video-audio-sync
```

或者下载 ZIP 文件并解压。

### 4. 安装 Python 依赖

```bash
pip install -r requirements.txt
```

### 5. 验证安装

运行测试脚本以验证安装是否成功：

#### Windows

```bash
run_tests.bat
```

#### macOS/Linux

```bash
./run_tests.sh
```

## 可能的问题及解决方案

### FFmpeg 未找到

如果遇到 "FFmpeg not found" 或类似错误，请确保 FFmpeg 已正确安装并添加到系统 PATH 中。

### OpenCV 安装问题

在某些系统上，OpenCV 安装可能需要额外的依赖。如果安装失败，请尝试：

#### Windows

```bash
pip install opencv-python-headless
```

#### Linux

```bash
sudo apt install libsm6 libxext6 libxrender-dev
pip install opencv-python
```

### 权限问题

如果在 Linux 或 macOS 上运行脚本时遇到权限问题，请确保脚本具有执行权限：

```bash
chmod +x run_tests.sh
chmod +x src/*.py
```

## 更多信息

更多详细信息，请参阅 [README.md](README.md) 文件。 