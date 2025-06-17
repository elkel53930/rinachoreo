#!/usr/bin/env python3
"""
Timeline controls with diagnostic timing information
This helps identify if the issue is in the timer, signal/slot, or rendering
"""

import time
import sys
from PyQt6.QtWidgets import (QWidget, QHBoxLayout, QPushButton, QSlider, 
                             QLabel, QDoubleSpinBox, QSpinBox, QVBoxLayout, QApplication)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal

class DiagnosticTimelineControls(QWidget):
    """タイムラインコントロールウィジェット with diagnostics"""
    
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
        
        # Diagnostic variables
        self.start_time = None
        self.last_real_time = None
        self.tick_count = 0
        self.diagnostics_enabled = True
        self.real_time_intervals = []
        self.processing_times = []
        
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Control buttons
        controls_layout = QHBoxLayout()
        
        # 再生ボタン
        self.play_button = QPushButton("▶")
        self.play_button.setFixedSize(40, 30)
        self.play_button.clicked.connect(self.toggle_play_pause)
        controls_layout.addWidget(self.play_button)
        
        # 停止ボタン
        self.stop_button = QPushButton("⏹")
        self.stop_button.setFixedSize(40, 30)
        self.stop_button.clicked.connect(self.stop)
        controls_layout.addWidget(self.stop_button)
        
        # 時間表示
        self.time_label = QLabel("00:00")
        self.time_label.setMinimumWidth(50)
        controls_layout.addWidget(self.time_label)
        
        # シークバー
        self.seek_slider = QSlider(Qt.Orientation.Horizontal)
        self.seek_slider.setMinimum(0)
        self.seek_slider.setMaximum(int(self.duration))
        self.seek_slider.setValue(0)
        self.seek_slider.valueChanged.connect(self.on_seek_changed)
        controls_layout.addWidget(self.seek_slider)
        
        # 合計時間表示
        self.duration_label = QLabel("05:00")
        self.duration_label.setMinimumWidth(50)
        controls_layout.addWidget(self.duration_label)
        
        # 再生速度
        controls_layout.addWidget(QLabel("Speed:"))
        self.speed_spinbox = QDoubleSpinBox()
        self.speed_spinbox.setRange(0.1, 3.0)
        self.speed_spinbox.setValue(1.0)
        self.speed_spinbox.setSingleStep(0.1)
        self.speed_spinbox.setSuffix("x")
        self.speed_spinbox.valueChanged.connect(self.on_speed_changed)
        controls_layout.addWidget(self.speed_spinbox)
        
        layout.addLayout(controls_layout)
        
        # Diagnostic display
        self.diagnostic_label = QLabel("Diagnostics: Ready")
        layout.addWidget(self.diagnostic_label)
        
        self.timing_label = QLabel("Timing info will appear here")
        layout.addWidget(self.timing_label)
        
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
            
            # Reset diagnostics
            self.start_time = time.time()
            self.last_real_time = self.start_time
            self.tick_count = 0
            self.real_time_intervals = []
            self.processing_times = []
            
            self.timer.start()
            self.play_pause_toggled.emit(True)
            print("Playback started - diagnostic mode enabled")
            
    def pause(self):
        """一時停止"""
        if self.is_playing:
            self.is_playing = False
            self.play_button.setText("▶")
            self.timer.stop()
            self.play_pause_toggled.emit(False)
            self.print_diagnostics()
            
    def stop(self):
        """停止"""
        self.pause()
        self.current_time = 0.0
        self.update_ui()
        self.time_changed.emit(self.current_time)
        
    def update_playback(self):
        """再生時の時間更新 with diagnostics"""
        frame_start = time.time()
        
        if self.is_playing:
            # Record real-time interval
            if self.last_real_time is not None:
                real_interval = (frame_start - self.last_real_time) * 1000
                self.real_time_intervals.append(real_interval)
                
            # Original timeline logic
            self.current_time += 20 * self.playback_speed  # 20ms * speed
            
            if self.current_time >= self.duration:
                self.current_time = 0.0  # 最初に戻す
                self.pause()
                return
                
            self.update_ui()
            self.time_changed.emit(self.current_time)
            
            self.tick_count += 1
            self.last_real_time = frame_start
            
        frame_end = time.time()
        processing_time = (frame_end - frame_start) * 1000
        self.processing_times.append(processing_time)
        
        # Update diagnostic display every second
        if self.tick_count % 50 == 0 and self.tick_count > 0:
            self.update_diagnostic_display()
            
    def update_diagnostic_display(self):
        """Update diagnostic information display"""
        if not self.real_time_intervals or not self.processing_times:
            return
            
        elapsed_real = time.time() - self.start_time
        expected_timeline_time = elapsed_real * 1000 * self.playback_speed
        timeline_error = abs(self.current_time - expected_timeline_time)
        
        recent_intervals = self.real_time_intervals[-50:] if len(self.real_time_intervals) >= 50 else self.real_time_intervals
        recent_processing = self.processing_times[-50:] if len(self.processing_times) >= 50 else self.processing_times
        
        avg_interval = sum(recent_intervals) / len(recent_intervals)
        avg_processing = sum(recent_processing) / len(recent_processing)
        
        diagnostic_text = f"Ticks: {self.tick_count} | Real FPS: {self.tick_count/elapsed_real:.1f} | Timeline: {self.current_time:.0f}ms"
        timing_text = f"Avg Interval: {avg_interval:.1f}ms | Processing: {avg_processing:.2f}ms | Error: {timeline_error:.0f}ms"
        
        self.diagnostic_label.setText(diagnostic_text)
        self.timing_label.setText(timing_text)
        
    def print_diagnostics(self):
        """Print detailed diagnostic information"""
        if not self.real_time_intervals or not self.processing_times:
            return
            
        total_real_time = time.time() - self.start_time
        expected_timeline_time = total_real_time * 1000 * self.playback_speed
        
        print("-" * 60)
        print("TIMELINE DIAGNOSTICS:")
        print(f"Real time elapsed: {total_real_time:.3f}s")
        print(f"Timeline time: {self.current_time:.0f}ms")
        print(f"Expected timeline time: {expected_timeline_time:.0f}ms")
        print(f"Timeline accuracy: {(self.current_time/expected_timeline_time)*100:.1f}%")
        print(f"Total ticks: {self.tick_count}")
        print(f"Real FPS: {self.tick_count/total_real_time:.1f}")
        
        avg_interval = sum(self.real_time_intervals) / len(self.real_time_intervals)
        min_interval = min(self.real_time_intervals)
        max_interval = max(self.real_time_intervals)
        
        avg_processing = sum(self.processing_times) / len(self.processing_times)
        max_processing = max(self.processing_times)
        
        print(f"Timer intervals - Avg: {avg_interval:.2f}ms, Min: {min_interval:.2f}ms, Max: {max_interval:.2f}ms")
        print(f"Processing times - Avg: {avg_processing:.3f}ms, Max: {max_processing:.3f}ms")
        
        # Analysis
        if avg_interval > 25:
            print("❌ ISSUE: Timer intervals are too long!")
        elif avg_interval < 15:
            print("❌ ISSUE: Timer intervals are too short!")
        else:
            print("✅ Timer intervals are reasonable")
            
        if avg_processing > 5:
            print("⚠️  WARNING: Frame processing is slow")
        else:
            print("✅ Frame processing is fast")
            
        accuracy = (self.current_time/expected_timeline_time)*100
        if accuracy < 95 or accuracy > 105:
            print("❌ ISSUE: Timeline is not running at correct speed!")
            if accuracy < 95:
                print("   → Timeline is running SLOWER than real-time")
            else:
                print("   → Timeline is running FASTER than real-time")
        else:
            print("✅ Timeline accuracy is good")
            
        print("-" * 60)
            
    def on_seek_changed(self, value):
        """シークバー変更"""
        if not self.is_playing:  # 再生中は無視
            self.current_time = float(value)
            self.update_ui()
            self.time_changed.emit(self.current_time)
            
    def on_speed_changed(self, speed):
        """再生速度変更"""
        self.playback_speed = speed
        
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

def main():
    app = QApplication(sys.argv)
    
    timeline = DiagnosticTimelineControls()
    timeline.show()
    timeline.setWindowTitle("Timeline Diagnostic Tool")
    timeline.resize(800, 200)
    
    print("Timeline Diagnostic Tool")
    print("- Click Play to start diagnostic playback")
    print("- The timeline will run for 5 seconds then loop")
    print("- Watch the diagnostic information for timing issues")
    print("- Click Pause to see detailed analysis")
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()