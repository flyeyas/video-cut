"""
用于将视频智能镜头分割与组合工具打包成Mac OS应用程序的setup脚本
使用py2app库进行打包
"""

from setuptools import setup

APP = ['video_tools_gui.py']
DATA_FILES = [
    ('src', ['src/video-combiner.py', 'src/split-video.py']),
    ('', ['requirements.txt', 'requirements_gui.txt', 'README.md'])
]
OPTIONS = {
    'argv_emulation': True,
    'iconfile': 'app_icon.icns',  # 如果有图标文件，请指定路径
    'plist': {
        'CFBundleName': '视频智能镜头分割与组合工具',
        'CFBundleDisplayName': '视频智能镜头分割与组合工具',
        'CFBundleGetInfoString': '视频智能镜头分割与组合工具',
        'CFBundleIdentifier': 'com.videotool.app',
        'CFBundleVersion': '1.0.0',
        'CFBundleShortVersionString': '1.0.0',
        'NSHumanReadableCopyright': 'Copyright © 2023',
    },
    'packages': ['PyQt5', 'moviepy', 'scenedetect', 'numpy', 'ffmpeg'],
    'includes': ['sip'],
    'excludes': ['tkinter', 'matplotlib'],
}

setup(
    app=APP,
    data_files=DATA_FILES,
    options={'py2app': OPTIONS},
    setup_requires=['py2app'],
    name='视频智能镜头分割与组合工具',
    version='1.0.0',
)