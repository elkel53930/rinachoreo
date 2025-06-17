#!/usr/bin/env python3
"""
Performance profiler for the motion editor components
This script measures the actual performance of each component to identify bottlenecks
"""

import time
import sys
import math
import numpy as np
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer, QObject

# Import the actual components
sys.path.append('src')
from graph_editor import GraphEditor, AxisGraph, ControlPoint
from preview_3d import Preview3D, OpenGLWidget

class PerformanceProfiler(QObject):
    """Performance profiler for motion editor components"""
    
    def __init__(self):
        super().__init__()
        
    def profile_graph_editor(self, iterations=1000):
        """Profile the GraphEditor get_angles_at_time performance"""
        print("Profiling GraphEditor.get_angles_at_time()...")
        
        # Create a graph editor with some test data
        graph_editor = GraphEditor()
        
        # Add some control points to make it realistic
        for axis_graph in [graph_editor.j1_graph, graph_editor.j2_graph, graph_editor.j3_graph]:
            axis_graph.points = [
                ControlPoint(0, 0),
                ControlPoint(1000, 0.5),
                ControlPoint(2000, -0.3),
                ControlPoint(3000, 0.8),
                ControlPoint(4000, -0.2),
                ControlPoint(5000, 0)
            ]
        
        times = []
        test_times = np.linspace(0, 5000, iterations)
        
        for i, test_time in enumerate(test_times):
            start = time.time()
            angles = graph_editor.get_angles_at_time(test_time)
            end = time.time()
            times.append((end - start) * 1000)  # Convert to ms
            
        avg_time = sum(times) / len(times)
        max_time = max(times)
        min_time = min(times)
        
        print(f"  Iterations: {iterations}")
        print(f"  Average time: {avg_time:.4f}ms")
        print(f"  Min time: {min_time:.4f}ms")
        print(f"  Max time: {max_time:.4f}ms")
        print(f"  Total time: {sum(times):.2f}ms for {iterations} calls")
        
        if avg_time > 1.0:
            print("  ⚠️  WARNING: Graph interpolation is slow (>1ms per call)")
        else:
            print("  ✅ Graph interpolation performance is good")
            
        return avg_time
        
    def profile_catmull_rom_spline(self, iterations=10000):
        """Profile the Catmull-Rom spline interpolation directly"""
        print("\nProfiling Catmull-Rom spline interpolation...")
        
        # Create an axis graph for testing
        axis_graph = AxisGraph("Test", "blue")
        
        times = []
        
        # Test with various t values
        test_values = np.linspace(0, 1, iterations)
        
        for t in test_values:
            start = time.time()
            # Call the spline interpolation directly
            result = axis_graph.catmull_rom_spline(-0.5, 0.0, 0.5, 0.3, t)
            end = time.time()
            times.append((end - start) * 1000)
            
        avg_time = sum(times) / len(times)
        max_time = max(times)
        
        print(f"  Iterations: {iterations}")
        print(f"  Average time: {avg_time:.6f}ms")
        print(f"  Max time: {max_time:.6f}ms")
        
        if avg_time > 0.01:
            print("  ⚠️  WARNING: Spline calculation is slow")
        else:
            print("  ✅ Spline calculation performance is good")
            
        return avg_time
        
    def profile_3d_preview_headless(self, iterations=100):
        """Profile 3D preview operations (headless mode)"""
        print("\nProfiling 3D Preview (headless mode)...")
        
        # We can't actually test OpenGL without a display context,
        # but we can test the angle processing parts
        times = []
        
        test_angles = [
            {'j1': 0.1, 'j2': 0.2, 'j3': 0.3},
            {'j1': -0.1, 'j2': -0.2, 'j3': -0.3},
            {'j1': 0.5, 'j2': 0.4, 'j3': 0.6},
            {'j1': -0.5, 'j2': -0.4, 'j3': -0.6}
        ]
        
        for i in range(iterations):
            angles = test_angles[i % len(test_angles)]
            
            start = time.time()
            
            # Simulate the math operations that would happen in update_pose
            j1_deg = math.degrees(angles.get('j1', 0))
            j2_deg = math.degrees(angles.get('j2', 0))
            j3_deg = math.degrees(angles.get('j3', 0))
            
            # Simulate some matrix calculations
            rotation_matrix = np.array([
                [math.cos(angles['j1']), -math.sin(angles['j1']), 0],
                [math.sin(angles['j1']), math.cos(angles['j1']), 0],
                [0, 0, 1]
            ])
            
            end = time.time()
            times.append((end - start) * 1000)
            
        avg_time = sum(times) / len(times)
        max_time = max(times)
        
        print(f"  Iterations: {iterations}")
        print(f"  Average time: {avg_time:.4f}ms")
        print(f"  Max time: {max_time:.4f}ms")
        
        print("  ⚠️  NOTE: This is only math operations, not actual OpenGL rendering")
        
        return avg_time
        
    def profile_timeline_simulation(self, duration_seconds=5):
        """Simulate the complete timeline playback chain"""
        print(f"\nProfiling complete timeline simulation for {duration_seconds} seconds...")
        
        # Create components
        graph_editor = GraphEditor()
        
        # Add realistic control points
        for axis_graph in [graph_editor.j1_graph, graph_editor.j2_graph, graph_editor.j3_graph]:
            axis_graph.points = [
                ControlPoint(0, 0),
                ControlPoint(1000, 0.5),
                ControlPoint(2000, -0.3),
                ControlPoint(3000, 0.8),
                ControlPoint(4000, -0.2),
                ControlPoint(5000, 0)
            ]
        
        # Simulate timeline playback
        current_time = 0.0
        playback_speed = 1.0
        frame_times = []
        
        start_time = time.time()
        tick_count = 0
        
        while current_time < duration_seconds * 1000:
            frame_start = time.time()
            
            # Simulate timeline update (same as timeline_controls.py)
            current_time += 20 * playback_speed
            
            # Get angles (this is the expensive part)
            angles = graph_editor.get_angles_at_time(current_time)
            
            # Simulate 3D update math (without OpenGL)
            j1_deg = math.degrees(angles.get('j1', 0))
            j2_deg = math.degrees(angles.get('j2', 0))
            j3_deg = math.degrees(angles.get('j3', 0))
            
            frame_end = time.time()
            frame_time = (frame_end - frame_start) * 1000
            frame_times.append(frame_time)
            
            tick_count += 1
            
            # Simulate the 20ms timer interval
            # (In reality this would be handled by QTimer)
            time.sleep(0.02)  # 20ms
            
        total_time = time.time() - start_time
        
        avg_frame_time = sum(frame_times) / len(frame_times)
        max_frame_time = max(frame_times)
        slow_frames = [t for t in frame_times if t > 20]  # Frames slower than timer interval
        
        print(f"  Total runtime: {total_time:.3f}s")
        print(f"  Total frames: {tick_count}")
        print(f"  Timeline final time: {current_time:.0f}ms")
        print(f"  Average frame time: {avg_frame_time:.3f}ms")
        print(f"  Max frame time: {max_frame_time:.3f}ms")
        print(f"  Slow frames (>20ms): {len(slow_frames)}/{len(frame_times)} ({len(slow_frames)/len(frame_times)*100:.1f}%)")
        
        # Analysis
        expected_timeline_time = duration_seconds * 1000
        timeline_accuracy = (current_time / expected_timeline_time) * 100
        print(f"  Timeline accuracy: {timeline_accuracy:.1f}%")
        
        if avg_frame_time > 20:
            print("  ❌ PROBLEM: Average frame time exceeds timer interval!")
            print("     This will cause timeline to run slower than real-time")
        elif len(slow_frames) > len(frame_times) * 0.05:  # More than 5% slow frames
            print("  ⚠️  WARNING: Frequent slow frames detected")
        else:
            print("  ✅ Frame timing performance is acceptable")
            
        return avg_frame_time

def main():
    # We need QApplication for some Qt components
    app = QApplication(sys.argv)
    
    profiler = PerformanceProfiler()
    
    print("=== MOTION EDITOR PERFORMANCE PROFILE ===")
    print()
    
    # Profile individual components
    graph_time = profiler.profile_graph_editor(1000)
    spline_time = profiler.profile_catmull_rom_spline(10000)
    preview_time = profiler.profile_3d_preview_headless(1000)
    
    # Profile complete system
    frame_time = profiler.profile_timeline_simulation(3)
    
    print("\n" + "="*50)
    print("SUMMARY:")
    print(f"Graph interpolation: {graph_time:.4f}ms per call")
    print(f"Spline calculation: {spline_time:.6f}ms per call")
    print(f"3D math operations: {preview_time:.4f}ms per call")
    print(f"Complete frame: {frame_time:.3f}ms per frame")
    
    print("\nRECOMMENDATIONS:")
    if graph_time > 0.5:
        print("• Consider optimizing graph interpolation")
        print("  - Cache interpolated values")
        print("  - Use lower-precision splines")
    
    if frame_time > 15:
        print("• Consider reducing computational load:")
        print("  - Lower 3D model complexity")
        print("  - Reduce interpolation points")
        print("  - Use separate thread for heavy calculations")
    elif frame_time < 5:
        print("• Performance is excellent - no optimizations needed")
    else:
        print("• Performance is acceptable for real-time playback")

if __name__ == "__main__":
    main()