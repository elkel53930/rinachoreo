#!/usr/bin/env python3
"""
Final comprehensive timing analysis
This script performs multiple tests to identify the root cause of timing issues
"""

import time
import sys
import statistics
from PyQt6.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QPushButton
from PyQt6.QtCore import QTimer, QObject, pyqtSignal, QThread

class SystemTimingTest(QObject):
    """Test system timing precision"""
    
    def __init__(self):
        super().__init__()
        self.results = {}
    
    def test_python_sleep_precision(self, iterations=100):
        """Test Python time.sleep() precision"""
        print("Testing Python time.sleep(0.02) precision...")
        
        times = []
        for i in range(iterations):
            start = time.time()
            time.sleep(0.02)  # 20ms
            end = time.time()
            actual_time = (end - start) * 1000
            times.append(actual_time)
            
        avg_time = statistics.mean(times)
        std_dev = statistics.stdev(times)
        
        print(f"  Average: {avg_time:.2f}ms (expected: 20.0ms)")
        print(f"  Std Dev: {std_dev:.2f}ms")
        print(f"  Min: {min(times):.2f}ms, Max: {max(times):.2f}ms")
        
        self.results['python_sleep'] = {
            'avg': avg_time,
            'std': std_dev,
            'accuracy': abs(20.0 - avg_time)
        }
        
        return avg_time
    
    def test_qtimer_precision(self, duration_seconds=3):
        """Test QTimer precision in event loop"""
        print(f"Testing QTimer precision for {duration_seconds} seconds...")
        
        self.timer_intervals = []
        self.timer_start_time = None
        self.timer_last_time = None
        self.timer_ticks = 0
        
        # Create timer
        timer = QTimer()
        timer.timeout.connect(self._on_timer_tick)
        timer.setInterval(20)  # 20ms
        
        # Start timing test
        self.timer_start_time = time.time()
        self.timer_last_time = self.timer_start_time
        timer.start()
        
        # Stop after duration
        stop_timer = QTimer()
        stop_timer.singleShot(duration_seconds * 1000, lambda: self._stop_timer_test(timer))
        
        return timer, stop_timer
    
    def _on_timer_tick(self):
        """Timer tick handler"""
        current_time = time.time()
        
        if self.timer_last_time is not None:
            interval = (current_time - self.timer_last_time) * 1000
            self.timer_intervals.append(interval)
            
        self.timer_ticks += 1
        self.timer_last_time = current_time
        
    def _stop_timer_test(self, timer):
        """Stop timer test and analyze"""
        timer.stop()
        
        if not self.timer_intervals:
            print("  No timer intervals recorded!")
            return
            
        total_time = time.time() - self.timer_start_time
        avg_interval = statistics.mean(self.timer_intervals)
        std_dev = statistics.stdev(self.timer_intervals)
        actual_fps = self.timer_ticks / total_time
        
        print(f"  Total time: {total_time:.3f}s")
        print(f"  Total ticks: {self.timer_ticks}")
        print(f"  Average interval: {avg_interval:.2f}ms (expected: 20.0ms)")
        print(f"  Std deviation: {std_dev:.2f}ms")
        print(f"  Actual FPS: {actual_fps:.1f} (expected: 50.0)")
        print(f"  Min: {min(self.timer_intervals):.2f}ms, Max: {max(self.timer_intervals):.2f}ms")
        
        self.results['qtimer'] = {
            'avg_interval': avg_interval,
            'std': std_dev,
            'fps': actual_fps,
            'accuracy': abs(20.0 - avg_interval)
        }
        
        # Continue with next test
        QTimer.singleShot(100, self.test_high_precision_timer)
    
    def test_high_precision_timer(self):
        """Test high precision timing using monotonic clock"""
        print("Testing high-precision timing...")
        
        intervals = []
        ticks = 0
        start_time = time.monotonic()
        last_time = start_time
        
        # Run for 2 seconds
        while time.monotonic() - start_time < 2.0:
            # Simulate 20ms intervals
            target_time = start_time + (ticks + 1) * 0.02
            
            # Busy wait until target time
            while time.monotonic() < target_time:
                pass
                
            current_time = time.monotonic()
            interval = (current_time - last_time) * 1000
            intervals.append(interval)
            
            ticks += 1
            last_time = current_time
            
        avg_interval = statistics.mean(intervals)
        std_dev = statistics.stdev(intervals)
        
        print(f"  Ticks: {ticks}")
        print(f"  Average interval: {avg_interval:.3f}ms")
        print(f"  Std deviation: {std_dev:.3f}ms")
        print(f"  Min: {min(intervals):.3f}ms, Max: {max(intervals):.3f}ms")
        
        self.results['high_precision'] = {
            'avg': avg_interval,
            'std': std_dev,
            'accuracy': abs(20.0 - avg_interval)
        }
        
        # Finish analysis
        QTimer.singleShot(100, self.analyze_results)
    
    def analyze_results(self):
        """Analyze all timing test results"""
        print("\n" + "="*60)
        print("TIMING ANALYSIS RESULTS:")
        print("="*60)
        
        if 'python_sleep' in self.results:
            ps = self.results['python_sleep']
            print(f"Python time.sleep(0.02):")
            print(f"  Average: {ps['avg']:.2f}ms, Accuracy: ±{ps['accuracy']:.2f}ms")
            if ps['accuracy'] > 5:
                print("  ❌ Python sleep timing is inaccurate")
            else:
                print("  ✅ Python sleep timing is acceptable")
        
        if 'qtimer' in self.results:
            qt = self.results['qtimer']
            print(f"QTimer intervals:")
            print(f"  Average: {qt['avg_interval']:.2f}ms, FPS: {qt['fps']:.1f}")
            if qt['accuracy'] > 2:
                print("  ❌ QTimer timing is inaccurate")
            elif qt['fps'] < 45 or qt['fps'] > 55:
                print("  ❌ QTimer FPS is out of range")
            else:
                print("  ✅ QTimer timing is good")
        
        if 'high_precision' in self.results:
            hp = self.results['high_precision']
            print(f"High-precision timing:")
            print(f"  Average: {hp['avg']:.3f}ms, Accuracy: ±{hp['accuracy']:.3f}ms")
            if hp['accuracy'] > 1:
                print("  ❌ High-precision timing shows system clock issues")
            else:
                print("  ✅ High-precision timing is excellent")
        
        print("\n" + "="*60)
        print("DIAGNOSIS:")
        
        # Compare results
        if 'qtimer' in self.results and 'high_precision' in self.results:
            qt_acc = self.results['qtimer']['accuracy']
            hp_acc = self.results['high_precision']['accuracy']
            
            if qt_acc > hp_acc * 2:
                print("❌ PROBLEM IDENTIFIED: QTimer is less accurate than high-precision timing")
                print("   → The issue is with Qt's timer implementation or event loop")
                print("   → This could be due to:")
                print("     - System load affecting Qt event processing")
                print("     - Qt timer resolution limitations")
                print("     - Display refresh rate conflicts (if using VSync)")
            elif qt_acc > 5:
                print("❌ PROBLEM IDENTIFIED: Both Qt and system timing are inaccurate")
                print("   → This is a system-level timing issue")
                print("   → Possible causes:")
                print("     - CPU power management (frequency scaling)")
                print("     - High system load")
                print("     - Virtual machine environment")
            else:
                print("✅ TIMING IS ACCURATE: The issue may be elsewhere")
                print("   → Check for:")
                print("     - 3D rendering performance")
                print("     - Signal/slot connection overhead")
                print("     - UI update blocking")
        
        print("\nRECOMMENDATIONS:")
        if 'qtimer' in self.results and self.results['qtimer']['fps'] < 45:
            print("• Use QTimer with SingleShot mode for more precise timing")
            print("• Consider using QElapsedTimer for more accurate time measurement")
            print("• Move heavy computations to separate threads")
        
        print("• In timeline_controls.py, consider using QElapsedTimer:")
        print("  - Track elapsed real time instead of counting timer ticks")
        print("  - This compensates for timer inaccuracies automatically")
        
        QApplication.instance().quit()

class TimingAnalysisWidget(QWidget):
    """Widget for running timing analysis"""
    
    def __init__(self):
        super().__init__()
        self.test_system = SystemTimingTest()
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        layout.addWidget(QLabel("Motion Editor Timing Analysis"))
        layout.addWidget(QLabel("This will test system and Qt timer precision"))
        
        self.status_label = QLabel("Ready to start analysis")
        layout.addWidget(self.status_label)
        
        start_button = QPushButton("Start Analysis")
        start_button.clicked.connect(self.start_analysis)
        layout.addWidget(start_button)
        
    def start_analysis(self):
        """Start the comprehensive timing analysis"""
        self.status_label.setText("Running analysis...")
        
        print("Starting comprehensive timing analysis...")
        print("This will test multiple timing methods to identify issues")
        print("-" * 60)
        
        # Start with Python sleep test (synchronous)
        self.test_system.test_python_sleep_precision(50)
        
        # Then start Qt timer test (asynchronous)
        QTimer.singleShot(100, self.start_qtimer_test)
        
    def start_qtimer_test(self):
        """Start the QTimer precision test"""
        timer, stop_timer = self.test_system.test_qtimer_precision(2)
        self.timer = timer  # Keep reference
        self.stop_timer = stop_timer

def main():
    app = QApplication(sys.argv)
    
    widget = TimingAnalysisWidget()
    widget.show()
    widget.setWindowTitle("Motion Editor Timing Analysis")
    widget.resize(400, 200)
    
    print("Motion Editor Timing Analysis Tool")
    print("Click 'Start Analysis' to begin comprehensive timing tests")
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()