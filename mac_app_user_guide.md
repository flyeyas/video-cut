# 视频智能镜头分割与组合工具 - Mac OS 用户指南

欢迎使用视频智能镜头分割与组合工具！本指南将帮助您在Mac OS系统上安装、配置和使用这款工具。

## 目录

1. [系统要求](#系统要求)
2. [安装方法](#安装方法)
3. [使用指南](#使用指南)
   - [视频镜头分割](#视频镜头分割)
   - [视频随机组合](#视频随机组合)
4. [常见问题](#常见问题)
5. [故障排除](#故障排除)

## 系统要求

- macOS 10.13 (High Sierra) 或更高版本
- 至少2GB可用内存
- 至少500MB可用磁盘空间（不包括视频文件存储空间）
- 建议使用多核处理器，以加快视频处理速度

## 安装方法

### 方法一：直接使用应用程序（推荐）

1. 下载 `视频智能镜头分割与组合工具.app.zip` 文件
2. 解压缩下载的文件
3. 将 `视频智能镜头分割与组合工具.app` 拖动到应用程序文件夹
4. 首次运行时，可能会出现安全警告，请按照以下步骤操作：
   - 在 Finder 中找到应用程序
   - 按住 Control 键并点击应用程序图标
   - 从快捷菜单中选择"打开"
   - 点击"打开"按钮

### 方法二：从源代码构建

如果您希望从源代码构建应用程序，请按照以下步骤操作：

1. 确保已安装 Python 3.6 或更高版本
2. 下载或克隆项目源代码
3. 打开终端，进入项目目录
4. 运行构建脚本：
   ```bash
   ./build_mac_app.sh
   ```
5. 构建完成后，应用程序将位于 `dist` 文件夹中

## 使用指南

启动应用程序后，您将看到一个包含两个标签页的界面：视频镜头分割和视频随机组合。

### 视频镜头分割

此功能可以将长视频自动分割成多个独立的场景片段。

#### 使用步骤：

1. **输入设置**
   - 点击"浏览..."按钮选择包含视频文件的输入文件夹
   - 点击"浏览..."按钮选择输出文件夹（分割后的视频片段将保存在此处）
   - 设置检测阈值（默认值为27.0，值越高分割越少，值越低分割越多）

2. **开始分割**
   - 点击"开始分割"按钮
   - 进度条将显示处理进度
   - 状态输出区域将显示详细的处理日志

3. **查看结果**
   - 处理完成后，您可以在指定的输出文件夹中找到分割后的视频片段
   - 每个片段的文件名格式为：原始文件名-场景编号.mp4

### 视频随机组合

此功能可以从视频库中随机选择片段并组合成新视频，支持根据音频时长自动确定目标时长。

#### 使用步骤：

1. **输入设置**
   - 点击"浏览..."按钮选择包含视频文件的输入文件夹
   - 点击"浏览..."按钮选择输出视频文件路径

2. **目标时长设置**（选择以下三种方式之一）
   - **手动指定时长**：直接输入目标视频时长（秒）
   - **从音频文件获取时长**：选择一个音频文件，系统将自动获取其时长作为目标时长
   - **从音频文件夹随机选择**：选择一个包含多个音频文件的文件夹，系统将随机选择一个音频文件并获取其时长

3. **高级设置**（可选）
   - **使用已分割的场景片段**：如果您已经使用视频镜头分割功能处理过视频，可以勾选此选项并选择场景片段文件夹
   - **设置最大裁剪时长**：限制自动裁剪时的最大片段时长（秒）

4. **开始组合**
   - 点击"开始组合"按钮
   - 进度条将显示处理进度
   - 状态输出区域将显示详细的处理日志

5. **查看结果**
   - 处理完成后，您可以在指定的输出路径找到生成的视频文件

## 常见问题

### 1. 应用程序无法启动

**问题**：双击应用程序图标后没有反应或出现"应用程序已损坏"的提示。

**解决方法**：
- 确认您的macOS版本满足系统要求
- 尝试通过Control+点击应用程序图标，然后选择"打开"
- 如果仍然无法打开，请打开"系统偏好设置" > "安全性与隐私"，在"通用"选项卡中点击"仍要打开"

### 2. 视频处理速度慢

**问题**：视频处理需要很长时间。

**解决方法**：
- 视频处理是计算密集型任务，处理时间与视频文件大小、分辨率和计算机性能有关
- 尝试使用较小分辨率的视频文件
- 关闭其他占用系统资源的应用程序
- 确保您的计算机有足够的冷却条件

### 3. 找不到分割后的视频片段

**问题**：视频镜头分割完成后，找不到输出的视频片段。

**解决方法**：
- 确认您已正确设置输出文件夹路径
- 检查状态输出区域是否有错误信息
- 如果视频中没有明显的场景变化，可能不会产生分割片段，尝试降低检测阈值

## 故障排除

如果您遇到其他问题，可以尝试以下步骤：

1. **重启应用程序**：完全退出应用程序后重新启动

2. **检查日志**：查看状态输出区域的详细日志信息

3. **重新安装**：卸载应用程序后重新安装

4. **检查依赖**：如果您是从源代码构建的应用程序，确保已安装所有必要的依赖

5. **联系支持**：如果问题仍然存在，请联系开发者获取支持

---

感谢您使用视频智能镜头分割与组合工具！希望这个工具能够帮助您更高效地处理视频内容。