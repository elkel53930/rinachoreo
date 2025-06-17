#!/usr/bin/env python3
"""
Playback timing test for the motion editor
This script tests the complete playback chain including signal/slot delays
"""

import time
import sys
import math
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QPushButton
from PyQt6.QtCore import QTimer, pyqtSignal, QObject

class MockGraphEditor(QObject):
    """Mock graph editor that simulates spline interpolation"""
    
    def __init__(self):
        super().__init__()
        self.computation_time = 0
        
    def get_angles_at_time(self, time_ms):
        """Simulate the angle calculation with some computational overhead"""
        start_time = time.time()
        
        # Simulate the cubic spline interpolation work
        # This mimics what the real graph editor does
        j1 = math.sin(time_ms * 0.001) * 0.5  # Simulate some computation
        j2 = math.cos(time_ms * 0.001) * 0.3
        j3 = math.sin(time_ms * 0.002) * 0.4
        
        # Add some computational overhead to simulate real spline calculation
        for _ in range(10):
            _ = math.sin(time_ms * 0.001 + _) * 0.1
            
        end_time = time.time()
        self.computation_time = (end_time - start_time) * 1000  # Convert to ms
        
        return {'j1': j1, 'j2': j2, 'j3': j3}

class MockPreview3D(QObject):
    """Mock 3D preview that simulates rendering overhead"""
    
    def __init__(self):
        super().__init__()
        self.update_time = 0
        
    def update_pose(self, angles):
        """Simulate 3D pose update with rendering overhead"""
        start_time = time.time()
        
        # Simulate OpenGL operations
        # In reality this would be matrix transformations, vertex updates, etc.
        for _ in range(50):  # Simulate some rendering work
            _ = math.sin(angles['j1']) + math.cos(angles['j2']) + math.tan(angles['j3'] + 0.001)
            
        end_time = time.time()
        self.update_time = (end_time - start_time) * 1000  # Convert to ms

class PlaybackTester(QWidget):
    """Complete playback system tester"""
    
    time_changed = pyqtSignal(float)
    
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
        self.last_time = None
        self.frame_times = []
        self.computation_times = []
        self.render_times = []
        
        self.setup_ui()
        self.time_changed.connect(self.on_time_changed)
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        self.status_label = QLabel("Ready to test")
        layout.addWidget(self.status_label)
        
        self.metrics_label = QLabel("Metrics will appear here")
        layout.addWidget(self.metrics_label)
        
        self.play_button = QPushButton("Start Test")
        self.play_button.clicked.connect(self.start_test)
        layout.addWidget(self.play_button)
        
    def start_test(self):
        """Start the playback test"""
        if self.is_playing:
            return
            
        print("Starting complete playback test...")
        print("This simulates the full timeline -> graph_editor -> 3D preview chain")
        print("-" * 60)
        
        self.start_time = time.time()
        self.last_time = self.start_time
        self.tick_count = 0
        self.current_time = 0.0
        self.frame_times = []
        self.computation_times = []
        self.render_times = []
        
        self.is_playing = True
        self.play_button.setText("Testing...")
        self.play_button.setEnabled(False)
        self.timer.start()
        
        # Stop after 5 seconds
        QTimer.singleShot(5000, self.stop_test)
        
    def update_playback(self):
        """Main playback update loop (same as timeline_controls.py)"""
        frame_start = time.time()
        
        if self.is_playing:
            # Same logic as timeline_controls.py
            self.current_time += 20 * self.playback_speed  # 20ms * speed
            
            if self.current_time >= self.duration:
                self.current_time = 0.0  # Loop back
                
            # Emit time change signal
            self.time_changed.emit(self.current_time)
            
        frame_end = time.time()
        frame_time = (frame_end - frame_start) * 1000  # Convert to ms
        
        self.frame_times.append(frame_time)
        self.computation_times.append(self.graph_editor.computation_time)
        self.render_times.append(self.preview_3d.update_time)
        
        self.tick_count += 1
        
        # Update UI every 50 ticks (~1 second)
        if self.tick_count % 50 == 0:
            elapsed = time.time() - self.start_time
            avg_frame_time = sum(self.frame_times[-50:]) / len(self.frame_times[-50:])
            avg_compute_time = sum(self.computation_times[-50:]) / len(self.computation_times[-50:])
            avg_render_time = sum(self.render_times[-50:]) / len(self.render_times[-50:])
            
            status = f"Time: {elapsed:.1f}s | Ticks: {self.tick_count} | Timeline: {self.current_time:.0f}ms"
            metrics = f"Frame: {avg_frame_time:.2f}ms | Compute: {avg_compute_time:.3f}ms | Render: {avg_render_time:.3f}ms"
            
            self.status_label.setText(status)
            self.metrics_label.setText(metrics)
            
            print(f"[{elapsed:.1f}s] Total: {avg_frame_time:.2f}ms (Compute: {avg_compute_time:.3f}ms, Render: {avg_render_time:.3f}ms)")
    
    def on_time_changed(self, time_ms):
        """Handle time change signal (same as main_window.py)"""
        # Get angles from graph editor (with computational overhead)
        angles = self.graph_editor.get_angles_at_time(time_ms)
        
        # Update 3D preview (with rendering overhead)
        self.preview_3d.update_pose(angles)
        
    def stop_test(self):
        """Stop test and analyze results"""
        self.timer.stop()
        self.is_playing = False
        
        total_time = time.time() - self.start_time
        actual_fps = self.tick_count / total_time
        
        print("-" * 60)
        print("COMPLETE PLAYBACK TEST RESULTS:")
        print(f"Total runtime: {total_time:.3f} seconds")
        print(f"Total frames: {self.tick_count}")
        print(f"Actual FPS: {actual_fps:.1f} (expected: 50.0)")
        print(f"Timeline final time: {self.current_time:.0f}ms (expected: ~{total_time*1000:.0f}ms)")
        
        if self.frame_times:
            avg_frame_time = sum(self.frame_times) / len(self.frame_times)
            max_frame_time = max(self.frame_times)
            avg_compute_time = sum(self.computation_times) / len(self.computation_times)
            avg_render_time = sum(self.render_times) / len(self.render_times)
            
            print(f"Average frame time: {avg_frame_time:.3f}ms")
            print(f"Maximum frame time: {max_frame_time:.3f}ms")
            print(f"Average computation time: {avg_compute_time:.3f}ms")
            print(f"Average render time: {avg_render_time:.3f}ms")
            
            # Performance analysis
            slow_frames = [t for t in self.frame_times if t > 25]  # Frames taking >25ms
            
            print(f"Slow frames (>25ms): {len(slow_frames)}/{len(self.frame_times)} ({len(slow_frames)/len(self.frame_times)*100:.1f}%)")
            
            # Real-time analysis
            expected_timeline_time = total_time * 1000  # Expected timeline progression in ms
            actual_timeline_time = self.current_time + (self.tick_count * 20)  # Account for loop-backs
            timeline_accuracy = (actual_timeline_time / expected_timeline_time) * 100
            
            print(f"Timeline accuracy: {timeline_accuracy:.1f}%")
            
        print("-" * 60)
        print("DIAGNOSIS:")
        
        if actual_fps < 45:
            print("❌ PROBLEM: Frame rate is too low!")
            print("   → Timeline will run slower than real-time")
        elif actual_fps > 55:
            print("❌ PROBLEM: Frame rate is too high!")
            print("   → Timeline will run faster than real-time")
        else:
            print("✅ Frame rate is acceptable")
            
        if avg_frame_time > 25:
            print("❌ PROBLEM: Frame processing is too slow!")
            print("   → Each frame takes longer than the 20ms timer interval")
            print("   → This will cause timeline lag")
        else:
            print("✅ Frame processing time is acceptable")
            
        if len(slow_frames) > len(self.frame_times) * 0.05:  # More than 5% slow frames
            print("⚠️  WARNING: Frequent frame drops detected")
            print("   → May cause jerky playback")
        else:
            print("✅ Frame consistency is good")
            
        # Recommendations
        print()
        print("RECOMMENDATIONS:")
        if avg_compute_time > 5:
            print("• Consider optimizing spline interpolation calculations")
        if avg_render_time > 10:
            print("• Consider optimizing 3D rendering (reduce polygon count, disable some effects)")
        if max_frame_time > 50:
            print("• Consider using a separate thread for heavy computations")
            
        self.play_button.setText("Test Complete")
        self.status_label.setText("Test completed - see console for results")
        self.metrics_label.setText("Check console output for detailed analysis")

def main():
    app = QApplication(sys.argv)
    
    tester = PlaybackTester()
    tester.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()