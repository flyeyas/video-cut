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

:: 检查并安装依赖
echo 正在检查依赖包...
pip show moviepy >nul 2>&1
if %errorlevel% neq 0 (
    echo 正在安装moviepy...
    pip install moviepy
)

pip show scenedetect >nul 2>&1
if %errorlevel% neq 0 (
    echo 正在安装scenedetect...
    pip install scenedetect
)

pip show numpy >nul 2>&1
if %errorlevel% neq 0 (
    echo 正在安装numpy...
    pip install numpy
)

pip show ffmpeg-python >nul 2>&1
if %errorlevel% neq 0 (
    echo 正在安装ffmpeg-python...
    pip install ffmpeg-python
)

:: 主菜单
:menu
cls
echo ===================================
echo    视频智能镜头分割与组合工具
echo ===================================
echo.
echo  1. 视频镜头分割
echo  2. 视频随机组合
echo  3. 退出
echo.
echo ===================================
echo.

set /p choice=请选择功能 (1-3): 

if "%choice%"=="1" goto split_video
if "%choice%"=="2" goto combine_video
if "%choice%"=="3" exit /b

echo 无效的选择，请重新输入。
timeout /t 2 >nul
goto menu

:: 视频镜头分割
:split_video
cls
echo ===================================
echo         视频镜头分割
echo ===================================
echo.
echo 请设置视频分割参数：
echo.

set /p input_folder=输入视频文件夹路径: 
set /p output_folder=输出视频文件夹路径: 

if not exist "%input_folder%" (
    echo 输入文件夹不存在！
    pause
    goto menu
)

if not exist "%output_folder%" (
    echo 输出文件夹不存在，是否创建？(Y/N)
    set /p create=
    if /i "!create!"=="Y" (
        mkdir "%output_folder%"
    ) else (
        echo 操作已取消。
        pause
        goto menu
    )
)

:: 修改split-video.py文件中的路径
echo 正在配置视频分割脚本...

:: 创建临时脚本文件
(
echo from scenedetect import open_video, SceneManager, split_video_ffmpeg
echo from scenedetect.detectors import ContentDetector
echo from scenedetect.video_splitter import split_video_ffmpeg
echo import os
echo import time
echo.
echo def split_video_into_scenes(video_path, output_path, threshold=27.0^):
echo     # Open our video, create a scene manager, and add a detector.
echo     video = open_video(video_path^)
echo     scene_manager = SceneManager(^)
echo     scene_manager.add_detector(
echo         ContentDetector(threshold=threshold^)^)
echo     scene_manager.detect_scenes(video, show_progress=True^)
echo     scene_list = scene_manager.get_scene_list(^)
echo     ret = split_video_ffmpeg(video_path, scene_list, output_dir=output_path, show_progress=True^)
echo     return ret
echo.
echo def split_video(folder_path, output_path^):
echo     file_list = os.listdir(folder_path^)
echo     for file_name in file_list:
echo         file_path = os.path.join(folder_path, file_name^)
echo         print(file_path, 'start......'^)
echo         try:
echo             ret = split_video_into_scenes(file_path, output_path^)
echo             print(file_path, 'end......，ret %%s' %% ret^)
echo         except Exception as e:
echo             print(file_path, 'end......，error %%s' %% e^)
echo         time.sleep(5^)
echo.
echo if __name__ == "__main__":
echo     folder_path = r"%input_folder%"
echo     output_path = r"%output_folder%"
echo     split_video(folder_path, output_path^)
) > temp_split_video.py

echo 开始执行视频分割...
python temp_split_video.py

del temp_split_video.py

echo.
echo 视频分割完成！
pause
goto menu

:: 视频随机组合
:combine_video
cls
echo ===================================
echo         视频随机组合
echo ===================================
echo.
echo 请设置视频组合参数：
echo.

set /p input_folder=输入视频文件夹路径: 
set /p output_file=输出视频文件路径(包含文件名): 

if not exist "%input_folder%" (
    echo 输入文件夹不存在！
    pause
    goto menu
)

echo.
echo 选择目标时长设置方式：
echo  1. 手动指定时长（秒）
echo  2. 从音频文件获取时长
echo  3. 从音频文件夹随机选择音频获取时长
echo.
set /p duration_choice=请选择 (1-3): 

set duration_param=

if "%duration_choice%"=="1" (
    set /p duration=请输入目标时长（秒）: 
    set duration_param=--duration !duration!
) else if "%duration_choice%"=="2" (
    set /p audio_file=请输入音频文件路径: 
    if not exist "!audio_file!" (
        echo 音频文件不存在！
        pause
        goto combine_video
    )
    set duration_param=--audio "!audio_file!"
) else if "%duration_choice%"=="3" (
    set /p audio_folder=请输入音频文件夹路径: 
    if not exist "!audio_folder!" (
        echo 音频文件夹不存在！
        pause
        goto combine_video
    )
    set duration_param=--audio_folder "!audio_folder!"
) else (
    echo 无效的选择！
    pause
    goto combine_video
)

echo.
echo 是否使用已分割的场景片段？(Y/N)
set /p use_scenes=

set scene_param=
if /i "%use_scenes%"=="Y" (
    set /p scene_folder=请输入场景片段文件夹路径: 
    if not exist "!scene_folder!" (
        echo 场景片段文件夹不存在！
        pause
        goto combine_video
    )
    set scene_param=--scene_folder "!scene_folder!"
)

echo.
echo 是否设置最大裁剪时长？(Y/N)
set /p set_max_clip=

set max_clip_param=
if /i "%set_max_clip%"=="Y" (
    set /p max_clip=请输入最大裁剪时长（秒）: 
    set max_clip_param=--max_clip_duration !max_clip!
)

echo 开始执行视频组合...
python src/video-combiner.py --input "%input_folder%" --output "%output_file%" %duration_param% %scene_param% %max_clip_param%

echo.
echo 视频组合完成！
pause
goto menu