@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

:: 设置标题
title 视频智能镜头分割与组合工具

:: 检查Python是否安装
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Python未安装，请先安装Python 3.6或更高版本。
    echo 可以从 https://www.python.org/downloads/ 下载安装。
    pause
    exit /b
)

:: 检查PyQt5是否安装
python -c "import PyQt5" >nul 2>&1
if %errorlevel% neq 0 (
    echo 正在安装GUI所需依赖...
    pip install -r requirements_gui.txt
    if %errorlevel% neq 0 (
        echo 安装依赖失败，请手动执行: pip install -r requirements_gui.txt
        pause
        exit /b
    )
)

:: 启动GUI应用
echo 正在启动视频智能镜头分割与组合工具...
python video_tools_gui.py

pause