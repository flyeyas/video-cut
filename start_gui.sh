#!/bin/bash

# 设置标题
echo "\033]0;视频智能镜头分割与组合工具\007"

# 检查Python是否安装
if ! command -v python3 &> /dev/null; then
    echo "Python未安装，请先安装Python 3.6或更高版本。"
    echo "可以从 https://www.python.org/downloads/ 下载安装。"
    read -p "按任意键退出..."
    exit 1
fi

# 检查PyQt5是否安装
if ! python3 -c "import PyQt5" &> /dev/null; then
    echo "正在安装GUI所需依赖..."
    pip3 install -r requirements_gui.txt
    if [ $? -ne 0 ]; then
        echo "安装依赖失败，请手动执行: pip3 install -r requirements_gui.txt"
        read -p "按任意键退出..."
        exit 1
    fi
fi

# 启动GUI应用
echo "正在启动视频智能镜头分割与组合工具..."
python3 video_tools_gui.py