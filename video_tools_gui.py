import os
import sys
import subprocess
import threading
import random
from PyQt5.QtWidgets import (QApplication, QMainWindow, QTabWidget, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QLineEdit, QPushButton, QFileDialog, 
                             QProgressBar, QMessageBox, QComboBox, QCheckBox, QSpinBox, 
                             QDoubleSpinBox, QGroupBox, QRadioButton, QButtonGroup, QTextEdit)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QTimer
from PyQt5.QtGui import QFont, QIcon, QPixmap

class WorkerThread(QThread):
    update_progress = pyqtSignal(int)
    update_status = pyqtSignal(str)
    finished = pyqtSignal(bool, str)
    
    def __init__(self, command):
        super().__init__()
        self.command = command
        
    def run(self):
        try:
            process = subprocess.Popen(
                self.command, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                shell=True
            )
            
            # 模拟进度更新
            progress = 0
            while process.poll() is None:
                output = process.stdout.readline()
                if output:
                    self.update_status.emit(output.strip())
                    # 根据输出内容更新进度
                    if "start......" in output:
                        progress += 5
                        self.update_progress.emit(min(progress, 95))
                    elif "end......" in output:
                        progress += 10
                        self.update_progress.emit(min(progress, 95))
            
            # 获取最终返回码
            return_code = process.wait()
            
            if return_code == 0:
                self.update_progress.emit(100)
                self.finished.emit(True, "操作成功完成！")
            else:
                self.finished.emit(False, f"操作失败，返回码: {return_code}")
                
        except Exception as e:
            self.finished.emit(False, f"发生错误: {str(e)}")

class VideoSplitTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        
        # 标题
        title_label = QLabel("视频镜头分割")
        title_label.setFont(QFont("Arial", 16, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # 输入视频文件夹
        input_group = QGroupBox("输入设置")
        input_layout = QVBoxLayout()
        
        input_folder_layout = QHBoxLayout()
        input_folder_layout.addWidget(QLabel("输入视频文件夹:"))
        self.input_folder_edit = QLineEdit()
        input_folder_layout.addWidget(self.input_folder_edit)
        self.browse_input_btn = QPushButton("浏览...")
        self.browse_input_btn.clicked.connect(self.browse_input_folder)
        input_folder_layout.addWidget(self.browse_input_btn)
        input_layout.addLayout(input_folder_layout)
        
        # 输出文件夹
        output_folder_layout = QHBoxLayout()
        output_folder_layout.addWidget(QLabel("输出文件夹:"))
        self.output_folder_edit = QLineEdit()
        output_folder_layout.addWidget(self.output_folder_edit)
        self.browse_output_btn = QPushButton("浏览...")
        self.browse_output_btn.clicked.connect(self.browse_output_folder)
        output_folder_layout.addWidget(self.browse_output_btn)
        input_layout.addLayout(output_folder_layout)
        
        # 阈值设置
        threshold_layout = QHBoxLayout()
        threshold_layout.addWidget(QLabel("检测阈值:"))
        self.threshold_spin = QDoubleSpinBox()
        self.threshold_spin.setRange(1.0, 100.0)
        self.threshold_spin.setValue(27.0)
        self.threshold_spin.setSingleStep(1.0)
        threshold_layout.addWidget(self.threshold_spin)
        threshold_layout.addStretch()
        input_layout.addLayout(threshold_layout)
        
        input_group.setLayout(input_layout)
        layout.addWidget(input_group)
        
        # 操作按钮
        self.start_btn = QPushButton("开始分割")
        self.start_btn.clicked.connect(self.start_split)
        layout.addWidget(self.start_btn)
        
        # 进度条
        progress_layout = QHBoxLayout()
        progress_layout.addWidget(QLabel("进度:"))
        self.progress_bar = QProgressBar()
        progress_layout.addWidget(self.progress_bar)
        layout.addLayout(progress_layout)
        
        # 状态输出
        status_group = QGroupBox("状态输出")
        status_layout = QVBoxLayout()
        self.status_text = QTextEdit()
        self.status_text.setReadOnly(True)
        status_layout.addWidget(self.status_text)
        status_group.setLayout(status_layout)
        layout.addWidget(status_group)
        
        self.setLayout(layout)
    
    def browse_input_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "选择输入视频文件夹")
        if folder:
            self.input_folder_edit.setText(folder)
    
    def browse_output_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "选择输出文件夹")
        if folder:
            self.output_folder_edit.setText(folder)
    
    def start_split(self):
        input_folder = self.input_folder_edit.text()
        output_folder = self.output_folder_edit.text()
        threshold = self.threshold_spin.value()
        
        if not input_folder or not output_folder:
            QMessageBox.warning(self, "警告", "请选择输入和输出文件夹！")
            return
        
        if not os.path.exists(input_folder):
            QMessageBox.warning(self, "警告", "输入文件夹不存在！")
            return
        
        if not os.path.exists(output_folder):
            reply = QMessageBox.question(self, "确认", "输出文件夹不存在，是否创建？",
                                        QMessageBox.Yes | QMessageBox.No, QMessageBox.Yes)
            if reply == QMessageBox.Yes:
                try:
                    os.makedirs(output_folder)
                except Exception as e:
                    QMessageBox.critical(self, "错误", f"创建文件夹失败: {str(e)}")
                    return
            else:
                return
        
        # 创建临时脚本
        script_content = f'''
        from scenedetect import open_video, SceneManager, split_video_ffmpeg
        from scenedetect.detectors import ContentDetector
        from scenedetect.video_splitter import split_video_ffmpeg
        import os
        import time

        def split_video_into_scenes(video_path, output_path, threshold={threshold}):
            # Open our video, create a scene manager, and add a detector.
            video = open_video(video_path)
            scene_manager = SceneManager()
            scene_manager.add_detector(
                ContentDetector(threshold=threshold))
            scene_manager.detect_scenes(video, show_progress=True)
            scene_list = scene_manager.get_scene_list()
            ret = split_video_ffmpeg(video_path, scene_list, output_dir=output_path, show_progress=True)
            return ret

        def split_video(folder_path, output_path):
            file_list = os.listdir(folder_path)
            for file_name in file_list:
                file_path = os.path.join(folder_path, file_name)
                print(file_path, 'start......')
                try:
                    ret = split_video_into_scenes(file_path, output_path)
                    print(file_path, 'end......，ret %s' % ret)
                except Exception as e:
                    print(file_path, 'end......，error %s' % e)
                time.sleep(1)

        if __name__ == "__main__":
            folder_path = r"{input_folder}"
            output_path = r"{output_folder}"
            split_video(folder_path, output_path)
        '''
        
        temp_script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "temp_split_video.py")
        with open(temp_script_path, "w", encoding="utf-8") as f:
            f.write(script_content)
        
        # 禁用按钮，重置进度条
        self.start_btn.setEnabled(False)
        self.progress_bar.setValue(0)
        self.status_text.clear()
        
        # 启动工作线程
        self.worker = WorkerThread(f"python \"{temp_script_path}\"")
        self.worker.update_progress.connect(self.update_progress)
        self.worker.update_status.connect(self.update_status)
        self.worker.finished.connect(self.on_finished)
        self.worker.start()
    
    def update_progress(self, value):
        self.progress_bar.setValue(value)
    
    def update_status(self, text):
        self.status_text.append(text)
        # 自动滚动到底部
        self.status_text.verticalScrollBar().setValue(self.status_text.verticalScrollBar().maximum())
    
    def on_finished(self, success, message):
        # 删除临时脚本
        temp_script_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "temp_split_video.py")
        if os.path.exists(temp_script_path):
            try:
                os.remove(temp_script_path)
            except:
                pass
        
        # 启用按钮
        self.start_btn.setEnabled(True)
        
        # 显示结果
        if success:
            QMessageBox.information(self, "完成", message)
        else:
            QMessageBox.critical(self, "错误", message)

class VideoCombineTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        
    def init_ui(self):
        layout = QVBoxLayout()
        
        # 标题
        title_label = QLabel("视频随机组合")
        title_label.setFont(QFont("Arial", 16, QFont.Bold))
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)
        
        # 输入设置
        input_group = QGroupBox("输入设置")
        input_layout = QVBoxLayout()
        
        # 输入视频文件夹
        input_folder_layout = QHBoxLayout()
        input_folder_layout.addWidget(QLabel("输入视频文件夹:"))
        self.input_folder_edit = QLineEdit()
        input_folder_layout.addWidget(self.input_folder_edit)
        self.browse_input_btn = QPushButton("浏览...")
        self.browse_input_btn.clicked.connect(self.browse_input_folder)
        input_folder_layout.addWidget(self.browse_input_btn)
        input_layout.addLayout(input_folder_layout)
        
        # 输出视频文件
        output_file_layout = QHBoxLayout()
        output_file_layout.addWidget(QLabel("输出视频文件:"))
        self.output_file_edit = QLineEdit()
        output_file_layout.addWidget(self.output_file_edit)
        self.browse_output_btn = QPushButton("浏览...")
        self.browse_output_btn.clicked.connect(self.browse_output_file)
        output_file_layout.addWidget(self.browse_output_btn)
        input_layout.addLayout(output_file_layout)
        
        input_group.setLayout(input_layout)
        layout.addWidget(input_group)
        
        # 时长设置
        duration_group = QGroupBox("目标时长设置")
        duration_layout = QVBoxLayout()
        
        # 时长选择方式
        self.duration_type_group = QButtonGroup(self)
        
        # 手动指定时长
        manual_radio = QRadioButton("手动指定时长")
        manual_radio.setChecked(True)
        self.duration_type_group.addButton(manual_radio, 1)
        duration_layout.addWidget(manual_radio)
        
        manual_layout = QHBoxLayout()
        manual_layout.addSpacing(20)
        manual_layout.addWidget(QLabel("目标时长(秒):"))
        self.duration_spin = QDoubleSpinBox()
        self.duration_spin.setRange(1.0, 3600.0)
        self.duration_spin.setValue(60.0)
        self.duration_spin.setSingleStep(1.0)
        manual_layout.addWidget(self.duration_spin)
        manual_layout.addStretch()
        duration_layout.addLayout(manual_layout)
        
        # 从音频文件获取时长
        audio_radio = QRadioButton("从音频文件获取时长")
        self.duration_type_group.addButton(audio_radio, 2)
        duration_layout.addWidget(audio_radio)
        
        audio_layout = QHBoxLayout()
        audio_layout.addSpacing(20)
        audio_layout.addWidget(QLabel("音频文件:"))
        self.audio_file_edit = QLineEdit()
        audio_layout.addWidget(self.audio_file_edit)
        self.browse_audio_btn = QPushButton("浏览...")
        self.browse_audio_btn.clicked.connect(self.browse_audio_file)
        audio_layout.addWidget(self.browse_audio_btn)
        duration_layout.addLayout(audio_layout)
        
        # 从音频文件夹随机选择
        audio_folder_radio = QRadioButton("从音频文件夹随机选择")
        self.duration_type_group.addButton(audio_folder_radio, 3)
        duration_layout.addWidget(audio_folder_radio)
        
        audio_folder_layout = QHBoxLayout()
        audio_folder_layout.addSpacing(20)
        audio_folder_layout.addWidget(QLabel("音频文件夹:"))
        self.audio_folder_edit = QLineEdit()
        audio_folder_layout.addWidget(self.audio_folder_edit)
        self.browse_audio_folder_btn = QPushButton("浏览...")
        self.browse_audio_folder_btn.clicked.connect(self.browse_audio_folder)
        audio_folder_layout.addWidget(self.browse_audio_folder_btn)
        duration_layout.addLayout(audio_folder_layout)
        
        duration_group.setLayout(duration_layout)
        layout.addWidget(duration_group)
        
        # 高级设置
        advanced_group = QGroupBox("高级设置")
        advanced_layout = QVBoxLayout()
        
        # 使用场景片段
        scene_layout = QHBoxLayout()
        self.use_scene_check = QCheckBox("使用已分割的场景片段")
        scene_layout.addWidget(self.use_scene_check)
        advanced_layout.addLayout(scene_layout)
        
        scene_folder_layout = QHBoxLayout()
        scene_folder_layout.addSpacing(20)
        scene_folder_layout.addWidget(QLabel("场景片段文件夹:"))
        self.scene_folder_edit = QLineEdit()
        scene_folder_layout.addWidget(self.scene_folder_edit)
        self.browse_scene_btn = QPushButton("浏览...")
        self.browse_scene_btn.clicked.connect(self.browse_scene_folder)
        scene_folder_layout.addWidget(self.browse_scene_btn)
        advanced_layout.addLayout(scene_folder_layout)
        
        # 最大裁剪时长
        clip_layout = QHBoxLayout()
        self.set_max_clip_check = QCheckBox("设置最大裁剪时长")
        clip_layout.addWidget(self.set_max_clip_check)
        advanced_layout.addLayout(clip_layout)
        
        max_clip_layout = QHBoxLayout()
        max_clip_layout.addSpacing(20)
        max_clip_layout.addWidget(QLabel("最大裁剪时长(秒):"))
        self.max_clip_spin = QDoubleSpinBox()
        self.max_clip_spin.setRange(1.0, 300.0)
        self.max_clip_spin.setValue(30.0)
        self.max_clip_spin.setSingleStep(1.0)
        max_clip_layout.addWidget(self.max_clip_spin)
        max_clip_layout.addStretch()
        advanced_layout.addLayout(max_clip_layout)
        
        advanced_group.setLayout(advanced_layout)
        layout.addWidget(advanced_group)
        
        # 操作按钮
        self.start_btn = QPushButton("开始组合")
        self.start_btn.clicked.connect(self.start_combine)
        layout.addWidget(self.start_btn)
        
        # 进度条
        progress_layout = QHBoxLayout()
        progress_layout.addWidget(QLabel("进度:"))
        self.progress_bar = QProgressBar()
        progress_layout.addWidget(self.progress_bar)
        layout.addLayout(progress_layout)
        
        # 状态输出
        status_group = QGroupBox("状态输出")
        status_layout = QVBoxLayout()
        self.status_text = QTextEdit()
        self.status_text.setReadOnly(True)
        status_layout.addWidget(self.status_text)
        status_group.setLayout(status_layout)
        layout.addWidget(status_group)
        
        self.setLayout(layout)
    
    def browse_input_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "选择输入视频文件夹")
        if folder:
            self.input_folder_edit.setText(folder)
    
    def browse_output_file(self):
        file, _ = QFileDialog.getSaveFileName(self, "选择输出视频文件", "", "视频文件 (*.mp4)")
        if file:
            self.output_file_edit.setText(file)
    
    def browse_audio_file(self):
        file, _ = QFileDialog.getOpenFileName(self, "选择音频文件", "", "音频文件 (*.mp3 *.wav *.aac *.flac *.ogg *.m4a)")
        if file:
            self.audio_file_edit.setText(file)
            # 自动选择对应的单选按钮
            self.duration_type_group.button(2).setChecked(True)
    
    def browse_audio_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "选择音频文件夹")
        if folder:
            self.audio_folder_edit.setText(folder)
            # 自动选择对应的单选按钮
            self.duration_type_group.button(3).setChecked(True)
    
    def browse_scene_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "选择场景片段文件夹")
        if folder:
            self.scene_folder_edit.setText(folder)
            # 自动勾选使用场景片段
            self.use_scene_check.setChecked(True)
    
    def start_combine(self):
        input_folder = self.input_folder_edit.text()
        output_file = self.output_file_edit.text()
        
        if not input_folder or not output_file:
            QMessageBox.warning(self, "警告", "请选择输入文件夹和输出文件！")
            return
        
        if not os.path.exists(input_folder):
            QMessageBox.warning(self, "警告", "输入文件夹不存在！")
            return
        
        # 构建命令
        cmd = ["python", "-c", "import sys; sys.path.append('./src'); import video_combiner"]
        cmd.append(f"--input \"{input_folder}\"")
        cmd.append(f"--output \"{output_file}\"")
        
        # 根据选择的时长类型添加参数
        duration_type = self.duration_type_group.checkedId()
        if duration_type == 1:  # 手动指定时长
            cmd.append(f"--duration {self.duration_spin.value()}")
        elif duration_type == 2:  # 从音频文件获取时长
            audio_file = self.audio_file_edit.text()
            if not audio_file or not os.path.exists(audio_file):
                QMessageBox.warning(self, "警告", "请选择有效的音频文件！")
                return
            cmd.append(f"--audio \"{audio_file}\"")
        elif duration_type == 3:  # 从音频文件夹随机选择
            audio_folder = self.audio_folder_edit.text()
            if not audio_folder or not os.path.exists(audio_folder):
                QMessageBox.warning(self, "警告", "请选择有效的音频文件夹！")
                return
            cmd.append(f"--audio_folder \"{audio_folder}\"")
        
        # 添加场景片段参数
        if self.use_scene_check.isChecked():
            scene_folder = self.scene_folder_edit.text()
            if not scene_folder or not os.path.exists(scene_folder):
                QMessageBox.warning(self, "警告", "请选择有效的场景片段文件夹！")
                return
            cmd.append(f"--scene_folder \"{scene_folder}\"")
        
        # 添加最大裁剪时长参数
        if self.set_max_clip_check.isChecked():
            cmd.append(f"--max_clip_duration {self.max_clip_spin.value()}")
        
        # 禁用按钮，重置进度条
        self.start_btn.setEnabled(False)
        self.progress_bar.setValue(0)
        self.status_text.clear()
        
        # 启动工作线程
        command = " ".join(cmd)
        self.worker = WorkerThread(command)
        self.worker.update_progress.connect(self.update_progress)
        self.worker.update_status.connect(self.update_status)
        self.worker.finished.connect(self.on_finished)
        self.worker.start()
    
    def update_progress(self, value):
        self.progress_bar.setValue(value)
    
    def update_status(self, text):
        self.status_text.append(text)
        # 自动滚动到底部
        self.status_text.verticalScrollBar().setValue(self.status_text.verticalScrollBar().maximum())
    
    def on_finished(self, success, message):
        # 启用按钮
        self.start_btn.setEnabled(True)
        
        # 显示结果
        if success:
            QMessageBox.information(self, "完成", message)
        else:
            QMessageBox.critical(self, "错误", message)

class VideoSortByRatioTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()
        
    def init_ui(self):
        # 创建布局
        main_layout = QVBoxLayout()
        
        # 输入文件夹选择
        input_group = QGroupBox("输入设置")
        input_layout = QVBoxLayout()
        
        input_folder_layout = QHBoxLayout()
        input_folder_layout.addWidget(QLabel("输入视频文件夹:"))
        self.input_folder_edit = QLineEdit()
        input_folder_layout.addWidget(self.input_folder_edit)
        browse_input_btn = QPushButton("浏览...")
        browse_input_btn.clicked.connect(self.browse_input_folder)
        input_folder_layout.addWidget(browse_input_btn)
        input_layout.addLayout(input_folder_layout)
        
        # 输出文件夹选择
        output_folder_layout = QHBoxLayout()
        output_folder_layout.addWidget(QLabel("输出根文件夹:"))
        self.output_folder_edit = QLineEdit()
        output_folder_layout.addWidget(self.output_folder_edit)
        browse_output_btn = QPushButton("浏览...")
        browse_output_btn.clicked.connect(self.browse_output_folder)
        output_folder_layout.addWidget(browse_output_btn)
        input_layout.addLayout(output_folder_layout)
        
        input_group.setLayout(input_layout)
        main_layout.addWidget(input_group)
        
        # 分类设置
        options_group = QGroupBox("分类设置")
        options_layout = QVBoxLayout()
        
        # 操作模式选择
        mode_layout = QHBoxLayout()
        mode_layout.addWidget(QLabel("操作模式:"))
        self.copy_mode_checkbox = QCheckBox("复制文件 (不移动原文件)")
        self.copy_mode_checkbox.setChecked(True)
        mode_layout.addWidget(self.copy_mode_checkbox)
        mode_layout.addStretch()
        options_layout.addLayout(mode_layout)
        
        # 比例范围选择
        ratio_layout = QHBoxLayout()
        ratio_layout.addWidget(QLabel("比例范围:"))
        self.ratio_mode_group = QButtonGroup()
        self.default_ratio_radio = QRadioButton("默认")
        self.custom_ratio_radio = QRadioButton("自定义")
        self.default_ratio_radio.setChecked(True)
        self.ratio_mode_group.addButton(self.default_ratio_radio)
        self.ratio_mode_group.addButton(self.custom_ratio_radio)
        ratio_layout.addWidget(self.default_ratio_radio)
        ratio_layout.addWidget(self.custom_ratio_radio)
        ratio_layout.addStretch()
        options_layout.addLayout(ratio_layout)
        
        options_group.setLayout(options_layout)
        main_layout.addWidget(options_group)
        
        # 默认比例范围说明
        ratio_info_group = QGroupBox("比例范围说明")
        ratio_info_layout = QVBoxLayout()
        
        ratio_info_text = QTextEdit()
        ratio_info_text.setReadOnly(True)
        ratio_info_text.setHtml("""
        <p><b>默认比例范围分类:</b></p>
        <ul>
            <li><b>竖屏窄视频_9-16</b>: 比例 < 0.5 (例如 9:16)</li>
            <li><b>竖屏视频_3-4</b>: 0.5 ≤ 比例 < 0.7 (例如 3:4)</li>
            <li><b>方形视频_1-1</b>: 0.7 ≤ 比例 < 1.2 (接近正方形)</li>
            <li><b>横屏视频_4-3</b>: 1.2 ≤ 比例 < 1.5 (例如 4:3)</li>
            <li><b>宽屏视频_16-9</b>: 1.5 ≤ 比例 < 1.9 (例如 16:9)</li>
            <li><b>超宽视频_21-9</b>: 比例 ≥ 1.9 (例如 21:9)</li>
        </ul>
        <p><b>自定义比例范围:</b></p>
        <ul>
            <li><b>竖屏视频_9-16</b>: 0.5 ≤ 比例 < 0.65</li>
            <li><b>竖屏视频_3-4</b>: 0.65 ≤ 比例 < 0.85</li>
            <li><b>方形视频_1-1</b>: 0.85 ≤ 比例 < 1.15</li>
            <li><b>横屏视频_4-3</b>: 1.15 ≤ 比例 < 1.4</li>
            <li><b>宽屏视频_16-9</b>: 1.4 ≤ 比例 < 1.9</li>
            <li><b>超宽视频_21-9</b>: 1.9 ≤ 比例 < 3.0</li>
        </ul>
        """)
        ratio_info_layout.addWidget(ratio_info_text)
        
        ratio_info_group.setLayout(ratio_info_layout)
        main_layout.addWidget(ratio_info_group)
        
        # 开始按钮
        start_layout = QHBoxLayout()
        self.start_button = QPushButton("开始分类")
        self.start_button.setMinimumHeight(40)
        self.start_button.clicked.connect(self.start_sort)
        start_layout.addWidget(self.start_button)
        main_layout.addLayout(start_layout)
        
        # 进度条
        progress_layout = QHBoxLayout()
        progress_layout.addWidget(QLabel("进度:"))
        self.progress_bar = QProgressBar()
        progress_layout.addWidget(self.progress_bar)
        main_layout.addLayout(progress_layout)
        
        # 状态输出
        status_layout = QVBoxLayout()
        status_layout.addWidget(QLabel("状态输出:"))
        self.status_output = QTextEdit()
        self.status_output.setReadOnly(True)
        status_layout.addWidget(self.status_output)
        main_layout.addLayout(status_layout)
        
        self.setLayout(main_layout)
        
    def browse_input_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "选择输入视频文件夹")
        if folder:
            self.input_folder_edit.setText(folder)
            
    def browse_output_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "选择输出根文件夹")
        if folder:
            self.output_folder_edit.setText(folder)
            
    def start_sort(self):
        input_folder = self.input_folder_edit.text()
        output_folder = self.output_folder_edit.text()
        
        if not input_folder or not output_folder:
            QMessageBox.warning(self, "输入错误", "请选择输入和输出文件夹")
            return
            
        if not os.path.exists(input_folder):
            QMessageBox.warning(self, "输入错误", f"输入文件夹不存在: {input_folder}")
            return
            
        # 准备命令
        copy_mode = "--copy" if self.copy_mode_checkbox.isChecked() else ""
        custom_mode = "--custom" if self.custom_ratio_radio.isChecked() else ""
        
        command = f'python "{os.path.join(os.path.dirname(os.path.abspath(__file__)), "src", "sort-videos-by-ratio.py")}" --input "{input_folder}" --output "{output_folder}" {copy_mode} {custom_mode}'
        
        # 更新UI状态
        self.start_button.setEnabled(False)
        self.progress_bar.setValue(0)
        self.status_output.clear()
        self.status_output.append(f"开始处理...\n命令: {command}\n")
        
        # 创建并启动工作线程
        self.worker_thread = WorkerThread(command)
        self.worker_thread.update_progress.connect(self.update_progress)
        self.worker_thread.update_status.connect(self.update_status)
        self.worker_thread.finished.connect(self.on_finished)
        self.worker_thread.start()
        
    def update_progress(self, value):
        self.progress_bar.setValue(value)
        
    def update_status(self, text):
        self.status_output.append(text)
        # 滚动到底部
        self.status_output.verticalScrollBar().setValue(self.status_output.verticalScrollBar().maximum())
        
    def on_finished(self, success, message):
        self.start_button.setEnabled(True)
        if success:
            self.progress_bar.setValue(100)
            self.status_output.append("\n处理完成!")
            QMessageBox.information(self, "处理完成", "视频按比例分类完成!")
        else:
            self.status_output.append(f"\n处理失败: {message}")
            QMessageBox.warning(self, "处理失败", f"视频按比例分类失败: {message}")

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.init_ui()
        
    def init_ui(self):
        self.setWindowTitle("视频智能镜头分割与组合工具")
        self.setMinimumSize(800, 600)
        
        # 创建标签页
        self.tabs = QTabWidget()
        self.split_tab = VideoSplitTab()
        self.combine_tab = VideoCombineTab()
        self.sort_ratio_tab = VideoSortByRatioTab()
        
        self.tabs.addTab(self.split_tab, "视频镜头分割")
        self.tabs.addTab(self.combine_tab, "视频随机组合")
        self.tabs.addTab(self.sort_ratio_tab, "视频按比例分类")
        
        self.setCentralWidget(self.tabs)
        
        # 检查依赖
        self.check_dependencies()
    
    def check_dependencies(self):
        missing_deps = []
        
        try:
            import moviepy
        except ImportError:
            missing_deps.append("moviepy")
        
        try:
            import scenedetect
        except ImportError:
            missing_deps.append("scenedetect")
        
        try:
            import numpy
        except ImportError:
            missing_deps.append("numpy")
        
        try:
            import ffmpeg
        except ImportError:
            missing_deps.append("ffmpeg-python")
        
        if missing_deps:
            reply = QMessageBox.question(
                self, 
                "缺少依赖", 
                f"检测到缺少以下依赖包: {', '.join(missing_deps)}\n\n是否立即安装？",
                QMessageBox.Yes | QMessageBox.No, 
                QMessageBox.Yes
            )
            
            if reply == QMessageBox.Yes:
                self.install_dependencies(missing_deps)
    
    def install_dependencies(self, deps):
        cmd = [sys.executable, "-m", "pip", "install"] + deps
        
        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True
            )
            
            output, _ = process.communicate()
            
            if process.returncode == 0:
                QMessageBox.information(self, "安装成功", "依赖包安装成功！")
            else:
                QMessageBox.warning(
                    self, 
                    "安装失败", 
                    f"依赖包安装失败，请手动安装:\n\npip install {' '.join(deps)}\n\n错误信息:\n{output}"
                )
        except Exception as e:
            QMessageBox.warning(
                self, 
                "安装失败", 
                f"依赖包安装失败，请手动安装:\n\npip install {' '.join(deps)}\n\n错误信息:\n{str(e)}"
            )

def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()