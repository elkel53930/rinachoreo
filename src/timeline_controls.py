from PyQt6.QtWidgets import (QWidget, QHBoxLayout, QPushButton, QSlider, 
                             QLabel, QDoubleSpinBox, QSpinBox)
from PyQt6.QtCore import Qt, QTimer, QElapsedTimer, pyqtSignal
from PyQt6.QtGui import QIcon

class TimelineControls(QWidget):
    """タイムラインコントロールウィジェット"""
    
    time_changed = pyqtSignal(float)  # time_ms
    play_pause_toggled = pyqtSignal(bool)  # is_playing
    
    def __init__(self):
        super().__init__()
        self.current_time = 0.0  # ms
        self.duration = 5000.0  # ms
        self.playback_speed = 1.0
        self.is_playing = False
        
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_playback)
        self.timer.setInterval(20)  # 50 FPS
        
        # 正確な時間計測用
        self.elapsed_timer = QElapsedTimer()
        self.playback_start_time = 0.0
        
        self.setup_ui()
        
    def setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 2, 5, 2)  # マージンを小さく
        
        # 再生ボタン
        self.play_button = QPushButton("▶")
        self.play_button.setFixedSize(30, 20)  # ボタンを小さく
        self.play_button.clicked.connect(self.toggle_play_pause)
        layout.addWidget(self.play_button)
        
        # 停止ボタン
        self.stop_button = QPushButton("⏹")
        self.stop_button.setFixedSize(30, 20)  # ボタンを小さく
        self.stop_button.clicked.connect(self.stop)
        layout.addWidget(self.stop_button)
        
        # 巻き戻しボタン
        self.rewind_button = QPushButton("⏮")
        self.rewind_button.setFixedSize(30, 20)  # ボタンを小さく
        self.rewind_button.clicked.connect(self.rewind)
        layout.addWidget(self.rewind_button)
        
        # 時間表示
        self.time_label = QLabel("00:00")
        self.time_label.setMinimumWidth(40)
        self.time_label.setMaximumHeight(20)
        layout.addWidget(self.time_label)
        
        # シークバー
        self.seek_slider = QSlider(Qt.Orientation.Horizontal)
        self.seek_slider.setMinimum(0)
        self.seek_slider.setMaximum(int(self.duration))
        self.seek_slider.setValue(0)
        self.seek_slider.setMaximumHeight(20)
        self.seek_slider.valueChanged.connect(self.on_seek_changed)
        layout.addWidget(self.seek_slider)
        
        # 合計時間表示
        self.duration_label = QLabel("05:00")
        self.duration_label.setMinimumWidth(40)
        self.duration_label.setMaximumHeight(20)
        layout.addWidget(self.duration_label)
        
        # 再生速度
        speed_label = QLabel("Speed:")
        speed_label.setMaximumHeight(20)
        layout.addWidget(speed_label)
        self.speed_spinbox = QDoubleSpinBox()
        self.speed_spinbox.setRange(0.1, 3.0)
        self.speed_spinbox.setValue(1.0)
        self.speed_spinbox.setSingleStep(0.1)
        self.speed_spinbox.setSuffix("x")
        self.speed_spinbox.setMaximumHeight(20)
        self.speed_spinbox.valueChanged.connect(self.on_speed_changed)
        layout.addWidget(self.speed_spinbox)
        
        # 長さ設定
        duration_label = QLabel("Duration:")
        duration_label.setMaximumHeight(20)
        layout.addWidget(duration_label)
        self.duration_spinbox = QSpinBox()
        self.duration_spinbox.setRange(1000, 60000)
        self.duration_spinbox.setValue(5000)
        self.duration_spinbox.setSuffix(" ms")
        self.duration_spinbox.setMaximumHeight(20)
        self.duration_spinbox.valueChanged.connect(self.on_duration_changed)
        layout.addWidget(self.duration_spinbox)
        
        # ウィジェット全体の最大高さを設定
        self.setMaximumHeight(30)
        
    def toggle_play_pause(self):
        """再生/停止切り替え"""
        if self.is_playing:
            self.pause()
        else:
            self.play()
            
    def play(self):
        """再生開始"""
        if not self.is_playing:
            self.is_playing = True
            self.play_button.setText("⏸")
            self.playback_start_time = self.current_time
            self.elapsed_timer.start()
            self.timer.start()
            self.play_pause_toggled.emit(True)
            
    def pause(self):
        """一時停止"""
        if self.is_playing:
            self.is_playing = False
            self.play_button.setText("▶")
            self.timer.stop()
            self.play_pause_toggled.emit(False)
            
    def stop(self):
        """停止"""
        self.pause()
        self.current_time = 0.0
        self.update_ui()
        self.time_changed.emit(self.current_time)
        
    def rewind(self):
        """巻き戻し"""
        self.current_time = 0.0
        self.update_ui()
        self.time_changed.emit(self.current_time)
        
    def update_playback(self):
        """再生時の時間更新"""
        if self.is_playing:
            # 実際の経過時間を使用してより正確な再生速度を実現
            elapsed_ms = self.elapsed_timer.elapsed()
            self.current_time = self.playback_start_time + (elapsed_ms * self.playback_speed)
            
            if self.current_time >= self.duration:
                self.current_time = 0.0  # 最初に戻す
                self.pause()
                
            self.update_ui()
            self.time_changed.emit(self.current_time)
            
    def on_seek_changed(self, value):
        """シークバー変更"""
        if not self.is_playing:  # 再生中は無視
            self.current_time = float(value)
            self.update_ui()
            self.time_changed.emit(self.current_time)
            
    def on_speed_changed(self, speed):
        """再生速度変更"""
        self.playback_speed = speed
        
    def on_duration_changed(self, duration):
        """長さ変更"""
        self.duration = float(duration)
        self.seek_slider.setMaximum(int(self.duration))
        self.update_ui()
        
        # 現在時刻が範囲外なら調整
        if self.current_time > self.duration:
            self.current_time = self.duration
            self.time_changed.emit(self.current_time)
            
    def update_ui(self):
        """UI更新"""
        # 時間表示
        current_sec = int(self.current_time / 1000)
        current_min = current_sec // 60
        current_sec = current_sec % 60
        self.time_label.setText(f"{current_min:02d}:{current_sec:02d}")
        
        duration_sec = int(self.duration / 1000)
        duration_min = duration_sec // 60
        duration_sec = duration_sec % 60
        self.duration_label.setText(f"{duration_min:02d}:{duration_sec:02d}")
        
        # シークバー
        self.seek_slider.blockSignals(True)
        self.seek_slider.setValue(int(self.current_time))
        self.seek_slider.blockSignals(False)
        
    def get_current_time(self):
        """現在時刻を取得"""
        return self.current_time
        
    def get_duration(self):
        """長さを取得"""
        return self.duration
        
    def set_duration(self, duration):
        """長さを設定"""
        self.duration = float(duration)
        self.duration_spinbox.setValue(int(duration))
        self.seek_slider.setMaximum(int(duration))
        self.update_ui()
        
    def reset(self):
        """リセット"""
        self.pause()
        self.current_time = 0.0
        self.duration = 5000.0
        self.playback_speed = 1.0
        self.duration_spinbox.setValue(5000)
        self.speed_spinbox.setValue(1.0)
        self.update_ui()
        
    def start_playback(self):
        """外部から再生開始"""
        self.play()
        
    def stop_playback(self):
        """外部から再生停止"""
        self.pause()