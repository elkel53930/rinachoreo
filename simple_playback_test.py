#!/usr/bin/env python3
"""
Simple playback timing test without GUI
"""

import time
import sys
import math
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer, QObject, pyqtSignal

class MockGraphEditor:
    """Mock graph editor that simulates spline interpolation"""
    
    def __init__(self):
        self.computation_time = 0
        
    def get_angles_at_time(self, time_ms):
        """Simulate the angle calculation with some computational overhead"""
        start_time = time.time()
        
        # Simulate cubic spline interpolation work
        j1 = math.sin(time_ms * 0.001) * 0.5
        j2 = math.cos(time_ms * 0.001) * 0.3
        j3 = math.sin(time_ms * 0.002) * 0.4
        
        # Add computational overhead
        for _ in range(20):
            _ = math.sin(time_ms * 0.001 + _) * 0.1
            
        self.computation_time = (time.time() - start_time) * 1000
        return {'j1': j1, 'j2': j2, 'j3': j3}

class MockPreview3D:
    """Mock 3D preview that simulates rendering overhead"""
    
    def __init__(self):
        self.update_time = 0
        
    def update_pose(self, angles):
        """Simulate 3D pose update with rendering overhead"""
        start_time = time.time()
        
        # Simulate OpenGL operations
        for _ in range(100):
            _ = math.sin(angles['j1']) + math.cos(angles['j2']) + math.tan(angles['j3'] + 0.001)
            
        self.update_time = (time.time() - start_time) * 1000

class SimplePlaybackTester(QObject):
    """Simple playback system tester"""
    
    def __init__(self):
        super().__init__()
        self.current_time = 0.0
        self.duration = 5000.0
        self.playback_speed = 1.0
        self.is_playing = False
        
        # Mock components
        self.graph_editor = MockGraphEditor()
        self.preview_3d = MockPreview3D()
        
        # Timer (same as timeline_controls.py)
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_playback)
        self.timer.setInterval(20)  # 50 FPS
        
        # Test metrics
        self.start_time = None
        self.tick_count = 0
        self.frame_times = []
        
    def start_test(self, duration_seconds=3):
        """Start the playback test"""
        print(f"Starting playback test for {duration_seconds} seconds...")
        print("Testing: Timer -> Graph Editor -> 3D Preview chain")
        print("-" * 50)
        
        self.start_time = time.time()
        self.tick_count = 0
        self.current_time = 0.0
        self.frame_times = []
        
        self.is_playing = True
        self.timer.start()
        
        # Stop after duration
        QTimer.singleShot(duration_seconds * 1000, self.stop_test)
        
    def update_playback(self):
        """Main playback update loop"""
        frame_start = time.time()
        
        if self.is_playing:
            # Same logic as timeline_controls.py
            self.current_time += 20 * self.playback_speed
            
            if self.current_time >= self.duration:
                self.current_time = 0.0
                
            # Simulate the signal/slot mechanism
            self.on_time_changed(self.current_time)
            
        frame_end = time.time()
        frame_time = (frame_end - frame_start) * 1000
        
        self.frame_times.append(frame_time)
        self.tick_count += 1
        
        # Print progress
        if self.tick_count % 50 == 0:
            elapsed = time.time() - self.start_time
            avg_frame_time = sum(self.frame_times[-50:]) / len(self.frame_times[-50:])
            print(f"[{elapsed:.1f}s] Ticks: {self.tick_count}, Avg frame time: {avg_frame_time:.2f}ms")
    
    def on_time_changed(self, time_ms):
        """Handle time change (same as main_window.py)"""
        angles = self.graph_editor.get_angles_at_time(time_ms)
        self.preview_3d.update_pose(angles)
        
    def stop_test(self):
        """Stop test and analyze results"""
        self.timer.stop()
        self.is_playing = False
        
        total_time = time.time() - self.start_time
        actual_fps = self.tick_count / total_time
        
        print("-" * 50)
        print("RESULTS:")
        print(f"Runtime: {total_time:.3f}s")
        print(f"Frames: {self.tick_count}")
        print(f"Actual FPS: {actual_fps:.1f}")
        print(f"Timeline time: {self.current_time:.0f}ms")
        
        if self.frame_times:
            avg_frame_time = sum(self.frame_times) / len(self.frame_times)
            max_frame_time = max(self.frame_times)
            slow_frames = [t for t in self.frame_times if t > 25]
            
            print(f"Avg frame time: {avg_frame_time:.2f}ms")
            print(f"Max frame time: {max_frame_time:.2f}ms")
            print(f"Slow frames: {len(slow_frames)}/{len(self.frame_times)}")
            
            if avg_frame_time > 20:
                print("❌ ISSUE: Frames taking longer than timer interval!")
                print("   This causes timeline to run slower than real-time")
            else:
                print("✅ Frame timing looks good")
                
        QApplication.instance().quit()

def main():
    app = QApplication(sys.argv)
    
    tester = SimplePlaybackTester()
    tester.start_test(3)  # Test for 3 seconds
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()