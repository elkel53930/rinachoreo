#!/usr/bin/env python3
"""
Timer precision test for timeline controls
This script tests the actual timing behavior of the PyQt6 QTimer
"""

import time
import sys
from PyQt6.QtWidgets import QApplication, QWidget
from PyQt6.QtCore import QTimer

class TimingTester(QWidget):
    def __init__(self):
        super().__init__()
        self.start_time = None
        self.tick_count = 0
        self.last_time = None
        self.intervals = []
        self.timer = QTimer()
        self.timer.timeout.connect(self.on_timer_tick)
        self.timer.setInterval(20)  # 20ms interval like in timeline_controls.py
        
    def start_test(self, duration_seconds=5):
        """Start timing test for specified duration"""
        print(f"Starting timer precision test for {duration_seconds} seconds...")
        print("Timer interval set to: 20ms (50 FPS)")
        print("Expected ticks per second: 50")
        print("Expected total ticks:", 50 * duration_seconds)
        print("-" * 50)
        
        self.start_time = time.time()
        self.last_time = self.start_time
        self.tick_count = 0
        self.intervals = []
        
        self.timer.start()
        
        # Stop after duration
        QTimer.singleShot(duration_seconds * 1000, self.stop_test)
        
    def on_timer_tick(self):
        """Timer tick handler"""
        current_time = time.time()
        
        if self.last_time is not None:
            interval = (current_time - self.last_time) * 1000  # Convert to ms
            self.intervals.append(interval)
            
        self.tick_count += 1
        self.last_time = current_time
        
        # Print progress every second
        elapsed = current_time - self.start_time
        if self.tick_count % 50 == 0:  # Every ~1 second
            print(f"Time: {elapsed:.1f}s, Ticks: {self.tick_count}, Avg interval: {sum(self.intervals[-50:])/len(self.intervals[-50:]):.1f}ms")
    
    def stop_test(self):
        """Stop test and analyze results"""
        self.timer.stop()
        
        total_time = time.time() - self.start_time
        actual_fps = self.tick_count / total_time
        
        print("-" * 50)
        print("RESULTS:")
        print(f"Total runtime: {total_time:.3f} seconds")
        print(f"Total ticks: {self.tick_count}")
        print(f"Expected ticks: {int(total_time * 50)}")
        print(f"Actual FPS: {actual_fps:.1f}")
        print(f"Expected FPS: 50.0")
        print(f"FPS accuracy: {(actual_fps/50.0)*100:.1f}%")
        
        if self.intervals:
            avg_interval = sum(self.intervals) / len(self.intervals)
            min_interval = min(self.intervals)
            max_interval = max(self.intervals)
            
            print(f"Average interval: {avg_interval:.2f}ms (expected: 20.00ms)")
            print(f"Min interval: {min_interval:.2f}ms")
            print(f"Max interval: {max_interval:.2f}ms")
            print(f"Interval accuracy: {(20.0/avg_interval)*100:.1f}%")
            
            # Check for significant deviations
            deviations = [abs(interval - 20) for interval in self.intervals]
            large_deviations = [d for d in deviations if d > 5]  # More than 5ms off
            
            print(f"Large deviations (>5ms): {len(large_deviations)}/{len(self.intervals)} ({len(large_deviations)/len(self.intervals)*100:.1f}%)")
        
        print("-" * 50)
        print("ANALYSIS:")
        
        if actual_fps < 45:
            print("⚠️  Timer is running significantly slower than expected!")
            print("   This could cause slow playback at 1x speed.")
        elif actual_fps > 55:
            print("⚠️  Timer is running significantly faster than expected!")
            print("   This could cause fast playback at 1x speed.")
        else:
            print("✅ Timer frequency is within acceptable range.")
            
        if self.intervals:
            if avg_interval > 25:
                print("⚠️  Average interval is too long - timeline will run slow.")
            elif avg_interval < 15:
                print("⚠️  Average interval is too short - timeline will run fast.")
            else:
                print("✅ Average interval is acceptable.")
                
            if len(large_deviations) > len(self.intervals) * 0.1:  # More than 10% deviations
                print("⚠️  High timing variability detected - may cause jerky playback.")
            else:
                print("✅ Timing consistency is good.")
        
        QApplication.instance().quit()

def main():
    app = QApplication(sys.argv)
    
    tester = TimingTester()
    tester.start_test(5)  # Test for 5 seconds
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()