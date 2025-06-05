# 视频智能镜头分割与组合工具 - Mac OS 应用程序打包指南

本文档将指导您如何将视频智能镜头分割与组合工具打包成一个独立的 Mac OS 应用程序。

## 准备工作

### 1. 安装必要的依赖

首先，您需要安装 py2app，这是一个用于将 Python 脚本打包成 Mac OS 应用程序的工具：

```bash
pip install py2app
```

同时确保已安装所有项目依赖：

```bash
pip install -r requirements_gui.txt
```

### 2. 准备应用图标

我们已经提供了一个 SVG 格式的图标文件 `app_icon.svg`，但 Mac OS 应用程序需要 `.icns` 格式的图标。您可以按照以下步骤将 SVG 转换为 ICNS：

#### 方法一：使用 Iconutil（推荐）

1. 首先将 SVG 转换为多个尺寸的 PNG 图像。您可以使用 Inkscape、GIMP 或在线转换工具。

2. 创建一个 iconset 文件夹：

```bash
mkdir app_icon.iconset
```

3. 将不同尺寸的 PNG 图像放入该文件夹，并按照以下命名规则命名：

```
icon_16x16.png
icon_16x16@2x.png (32x32)
icon_32x32.png
icon_32x32@2x.png (64x64)
icon_128x128.png
icon_128x128@2x.png (256x256)
icon_256x256.png
icon_256x256@2x.png (512x512)
icon_512x512.png
icon_512x512@2x.png (1024x1024)
```

4. 使用 iconutil 命令将 iconset 转换为 icns：

```bash
iconutil -c icns app_icon.iconset -o app_icon.icns
```

#### 方法二：使用第三方工具

您也可以使用第三方工具如 Image2Icon 或在线转换服务将 SVG 直接转换为 ICNS 格式。

## 打包应用程序

### 1. 清理之前的构建（如果有）

```bash
rm -rf build dist
```

### 2. 使用 py2app 打包应用程序

我们已经提供了一个配置好的 `setup.py` 文件，您可以直接使用它来打包应用程序：

```bash
python setup.py py2app
```

这个过程可能需要几分钟时间，取决于您的计算机性能和项目依赖的大小。

### 3. 测试应用程序

打包完成后，您可以在 `dist` 文件夹中找到打包好的应用程序：

```bash
open dist/视频智能镜头分割与组合工具.app
```

## 常见问题解决

### 1. 应用程序无法启动

如果应用程序无法启动，您可以通过终端查看错误信息：

```bash
/Applications/视频智能镜头分割与组合工具.app/Contents/MacOS/视频智能镜头分割与组合工具
```

### 2. 缺少依赖

如果应用程序启动时报错缺少某些依赖，您可以修改 `setup.py` 文件中的 `packages` 列表，添加缺少的依赖，然后重新打包。

### 3. 文件权限问题

如果应用程序无法访问某些文件，可能是因为 Mac OS 的安全机制。您可以尝试在应用程序的 Info.plist 文件中添加相应的权限声明，或者指导用户在「系统偏好设置」中授予应用程序必要的权限。

## 分发应用程序

打包好的应用程序可以直接分发给其他 Mac 用户使用。您可以：

1. 将整个 `.app` 文件夹压缩成 ZIP 文件
2. 创建一个 DMG 安装镜像（需要额外的工具）
3. 上传到您的网站或文件分享服务

注意：如果您计划公开分发应用程序，建议使用 Apple Developer 账号对应用程序进行签名，以避免用户在运行时遇到安全警告。

## 其他优化建议

1. **减小应用体积**：py2app 默认会包含许多可能不需要的库。您可以在 `setup.py` 中的 `excludes` 列表中添加不需要的库。

2. **添加启动画面**：您可以修改应用程序的 Info.plist 文件，添加启动画面配置。

3. **本地化**：如果您计划支持多语言，可以添加本地化资源文件。

4. **自动更新**：考虑实现自动更新功能，以便用户能够获取最新版本。