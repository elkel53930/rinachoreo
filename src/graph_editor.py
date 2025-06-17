import math
import numpy as np
from scipy.interpolate import CubicSpline
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QDoubleSpinBox, QCheckBox, QPushButton, QFrame)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QPointF
from PyQt6.QtGui import QPainter, QPen, QBrush, QColor, QFont

class ControlPoint:
    def __init__(self, time_ms, angle_rad):
        self.time_ms = time_ms
        self.angle_rad = angle_rad
        self.selected = False

class AxisGraph(QWidget):
    """単一軸のグラフウィジェット"""
    
    motion_changed = pyqtSignal()
    
    def __init__(self, axis_name, color, min_angle=-math.pi/2, max_angle=math.pi/2):
        super().__init__()
        self.axis_name = axis_name
        self.color = QColor(color)
        self.min_angle = min_angle
        self.max_angle = max_angle
        self.points = [ControlPoint(0, 0), ControlPoint(5000, 0)]  # 初期点
        self.selected_point = None
        self.dragging = False
        self.snap_enabled = True
        self.grid_time = 100  # ms
        
        self.setMinimumHeight(150)
        self.setMouseTracking(True)
        
        # Undo/Redoスタック
        self.undo_stack = []
        self.redo_stack = []
        
    def save_state(self):
        """現在の状態をUndoスタックに保存"""
        state = [(p.time_ms, p.angle_rad) for p in self.points]
        self.undo_stack.append(state)
        self.redo_stack.clear()
        if len(self.undo_stack) > 50:  # スタックサイズ制限
            self.undo_stack.pop(0)
            
    def undo(self):
        if self.undo_stack:
            current_state = [(p.time_ms, p.angle_rad) for p in self.points]
            self.redo_stack.append(current_state)
            
            state = self.undo_stack.pop()
            self.points = [ControlPoint(t, a) for t, a in state]
            self.selected_point = None
            self.update()
            self.motion_changed.emit()
            
    def redo(self):
        if self.redo_stack:
            current_state = [(p.time_ms, p.angle_rad) for p in self.points]
            self.undo_stack.append(current_state)
            
            state = self.redo_stack.pop()
            self.points = [ControlPoint(t, a) for t, a in state]
            self.selected_point = None
            self.update()
            self.motion_changed.emit()
    
    def time_to_x(self, time_ms):
        """時間をX座標に変換"""
        margin = 40
        return margin + (time_ms / 5000.0) * (self.width() - 2 * margin)
    
    def x_to_time(self, x):
        """X座標を時間に変換"""
        margin = 40
        return ((x - margin) / (self.width() - 2 * margin)) * 5000.0
    
    def angle_to_y(self, angle_rad):
        """角度をY座標に変換"""
        margin = 30
        norm = (angle_rad - self.min_angle) / (self.max_angle - self.min_angle)
        return self.height() - margin - norm * (self.height() - 2 * margin)
    
    def y_to_angle(self, y):
        """Y座標を角度に変換"""
        margin = 30
        norm = (self.height() - margin - y) / (self.height() - 2 * margin)
        return self.min_angle + norm * (self.max_angle - self.min_angle)
    
    def snap_time(self, time_ms):
        """時間をグリッドにスナップ"""
        if self.snap_enabled:
            return round(time_ms / self.grid_time) * self.grid_time
        return time_ms
    
    def get_point_at_pos(self, x, y, tolerance=10):
        """指定位置にある制御点を取得"""
        for point in self.points:
            px = self.time_to_x(point.time_ms)
            py = self.angle_to_y(point.angle_rad)
            if abs(px - x) <= tolerance and abs(py - y) <= tolerance:
                return point
        return None
    
    def add_point(self, time_ms, angle_rad):
        """制御点を追加"""
        self.save_state()
        
        time_ms = max(0, min(5000, time_ms))
        angle_rad = max(self.min_angle, min(self.max_angle, angle_rad))
        
        # 挿入位置を決定
        insert_idx = 0
        for i, point in enumerate(self.points):
            if point.time_ms < time_ms:
                insert_idx = i + 1
            else:
                break
                
        new_point = ControlPoint(time_ms, angle_rad)
        self.points.insert(insert_idx, new_point)
        self.selected_point = new_point
        self.update()
        self.motion_changed.emit()
    
    def delete_point(self, point):
        """制御点を削除"""
        if len(self.points) <= 2:  # 最低2点は残す
            return
            
        self.save_state()
        self.points.remove(point)
        if self.selected_point == point:
            self.selected_point = None
        self.update()
        self.motion_changed.emit()
    
    def move_point(self, point, new_time, new_angle):
        """制御点を移動"""
        # 制約チェック
        idx = self.points.index(point)
        
        # 時間制約（他の点を越えない）
        min_time = self.points[idx-1].time_ms if idx > 0 else 0
        max_time = self.points[idx+1].time_ms if idx < len(self.points)-1 else 5000
        new_time = max(min_time, min(max_time, new_time))
        
        # 角度制約
        new_angle = max(self.min_angle, min(self.max_angle, new_angle))
        
        point.time_ms = self.snap_time(new_time)
        point.angle_rad = new_angle
        
        self.update()
        self.motion_changed.emit()
    
    def catmull_rom_spline(self, p0, p1, p2, p3, t):
        """Catmull-Romスプライン補間"""
        return 0.5 * ((2 * p1) +
                     (-p0 + p2) * t +
                     (2*p0 - 5*p1 + 4*p2 - p3) * t * t +
                     (-p0 + 3*p1 - 3*p2 + p3) * t * t * t)
    
    def get_interpolated_value(self, time_ms):
        """指定時刻でのCatmull-Romスプライン補間値を取得"""
        if len(self.points) < 2:
            return 0
            
        times = [p.time_ms for p in self.points]
        angles = [p.angle_rad for p in self.points]
        
        if time_ms <= times[0]:
            return angles[0]
        if time_ms >= times[-1]:
            return angles[-1]
            
        # Catmull-Romスプライン補間
        for i in range(len(times) - 1):
            if times[i] <= time_ms <= times[i + 1]:
                # 制御点を4つ準備（境界の場合は端点を複製）
                p0 = angles[max(0, i-1)]
                p1 = angles[i]
                p2 = angles[i+1]
                p3 = angles[min(len(angles)-1, i+2)]
                
                # 正規化されたパラメータt (0-1)
                t = (time_ms - times[i]) / (times[i + 1] - times[i])
                
                return self.catmull_rom_spline(p0, p1, p2, p3, t)
        
        return 0
    
    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # 背景
        painter.fillRect(self.rect(), QColor(250, 250, 250))
        
        # グリッド描画
        self.draw_grid(painter)
        
        # 曲線描画
        self.draw_curve(painter)
        
        # 制御点描画
        self.draw_points(painter)
        
        # 軸ラベル
        self.draw_labels(painter)
    
    def draw_grid(self, painter):
        """グリッド描画"""
        pen = QPen(QColor(220, 220, 220))
        painter.setPen(pen)
        
        margin = 40
        
        # 縦線（時間グリッド）
        for t in range(0, 5001, 500):
            x = int(self.time_to_x(t))
            painter.drawLine(x, 0, x, self.height())
        
        # 横線（角度グリッド）
        for angle in np.linspace(self.min_angle, self.max_angle, 5):
            y = int(self.angle_to_y(angle))
            painter.drawLine(margin, y, self.width() - margin, y)
    
    def draw_curve(self, painter):
        """補間曲線描画"""
        if len(self.points) < 2:
            return
            
        pen = QPen(self.color, 2)
        painter.setPen(pen)
        
        # 曲線をセグメントに分けて描画
        prev_x = int(self.time_to_x(self.points[0].time_ms))
        prev_y = int(self.angle_to_y(self.points[0].angle_rad))
        
        for t in range(0, 5001, 10):
            angle = self.get_interpolated_value(t)
            x = int(self.time_to_x(t))
            y = int(self.angle_to_y(angle))
            painter.drawLine(prev_x, prev_y, x, y)
            prev_x, prev_y = x, y
    
    def draw_points(self, painter):
        """制御点描画"""
        for point in self.points:
            x = int(self.time_to_x(point.time_ms))
            y = int(self.angle_to_y(point.angle_rad))
            
            # 点の色
            if point == self.selected_point:
                brush = QBrush(QColor(255, 0, 0))
                pen = QPen(QColor(150, 0, 0), 2)
            else:
                brush = QBrush(self.color)
                pen = QPen(self.color.darker(), 2)
            
            painter.setPen(pen)
            painter.setBrush(brush)
            painter.drawEllipse(x - 5, y - 5, 10, 10)
    
    def draw_labels(self, painter):
        """ラベル描画"""
        font = QFont()
        font.setPointSize(10)
        painter.setFont(font)
        painter.setPen(QPen(Qt.GlobalColor.black))
        
        # 軸名
        painter.drawText(10, 20, f"{self.axis_name}")
        
        # 角度範囲
        margin = 40
        painter.drawText(5, int(self.angle_to_y(self.max_angle)), f"{self.max_angle:.2f}")
        painter.drawText(5, int(self.angle_to_y(self.min_angle)), f"{self.min_angle:.2f}")
        
        # 時間
        painter.drawText(int(self.time_to_x(0)) - 10, self.height() - 5, "0")
        painter.drawText(int(self.time_to_x(5000)) - 20, self.height() - 5, "5000")
    
    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            point = self.get_point_at_pos(event.position().x(), event.position().y())
            if point:
                self.selected_point = point
                self.dragging = True
                self.save_state()
            else:
                self.selected_point = None
            self.update()
            
        elif event.button() == Qt.MouseButton.RightButton:
            point = self.get_point_at_pos(event.position().x(), event.position().y())
            if point:
                self.delete_point(point)
    
    def mouseDoubleClickEvent(self, event):
        """ダブルクリックで制御点追加"""
        time_ms = self.x_to_time(event.position().x())
        angle_rad = self.y_to_angle(event.position().y())
        self.add_point(time_ms, angle_rad)
    
    def mouseMoveEvent(self, event):
        if self.dragging and self.selected_point:
            new_time = self.x_to_time(event.position().x())
            new_angle = self.y_to_angle(event.position().y())
            self.move_point(self.selected_point, new_time, new_angle)
    
    def mouseReleaseEvent(self, event):
        self.dragging = False

class GraphEditor(QWidget):
    """グラフエディタメインウィジェット"""
    
    motion_changed = pyqtSignal()
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # コントロールパネル
        control_panel = QFrame()
        control_panel.setFrameStyle(QFrame.Shape.StyledPanel)
        control_layout = QHBoxLayout(control_panel)
        
        # Snap設定
        self.snap_checkbox = QCheckBox("Snap to Grid")
        self.snap_checkbox.setChecked(True)
        self.snap_checkbox.toggled.connect(self.on_snap_toggled)
        control_layout.addWidget(self.snap_checkbox)
        
        # 選択点の値編集
        control_layout.addWidget(QLabel("Selected Point:"))
        control_layout.addWidget(QLabel("Time:"))
        self.time_spinbox = QDoubleSpinBox()
        self.time_spinbox.setRange(0, 5000)
        self.time_spinbox.setSuffix(" ms")
        control_layout.addWidget(self.time_spinbox)
        
        control_layout.addWidget(QLabel("Angle:"))
        self.angle_spinbox = QDoubleSpinBox()
        self.angle_spinbox.setRange(-math.pi/2, math.pi/2)
        self.angle_spinbox.setSuffix(" rad")
        self.angle_spinbox.setDecimals(3)
        control_layout.addWidget(self.angle_spinbox)
        
        control_layout.addStretch()
        layout.addWidget(control_panel)
        
        # 軸グラフ
        self.j1_graph = AxisGraph("J1 (Yaw)", "blue")
        self.j2_graph = AxisGraph("J2 (Roll)", "green") 
        self.j3_graph = AxisGraph("J3 (Pitch)", "red")
        
        for graph in [self.j1_graph, self.j2_graph, self.j3_graph]:
            graph.motion_changed.connect(self.motion_changed.emit)
            layout.addWidget(graph)
            
    def on_snap_toggled(self, checked):
        """スナップ設定変更"""
        for graph in [self.j1_graph, self.j2_graph, self.j3_graph]:
            graph.snap_enabled = checked
            
    def get_angles_at_time(self, time_ms):
        """指定時刻での各軸角度を取得"""
        return {
            'j1': self.j1_graph.get_interpolated_value(time_ms),
            'j2': self.j2_graph.get_interpolated_value(time_ms),
            'j3': self.j3_graph.get_interpolated_value(time_ms)
        }
    
    def get_motion_data(self):
        """モーションデータを取得"""
        return {
            'j1': [(p.time_ms, p.angle_rad) for p in self.j1_graph.points],
            'j2': [(p.time_ms, p.angle_rad) for p in self.j2_graph.points],
            'j3': [(p.time_ms, p.angle_rad) for p in self.j3_graph.points]
        }
    
    def load_data(self, data):
        """データを読み込み"""
        motion_data = data.get('motion_data', {})
        
        for axis, graph in [('j1', self.j1_graph), ('j2', self.j2_graph), ('j3', self.j3_graph)]:
            if axis in motion_data:
                graph.points = [ControlPoint(t, a) for t, a in motion_data[axis]]
                graph.update()
    
    def get_angle_ranges(self):
        """角度範囲を取得"""
        return {
            'j1': (self.j1_graph.min_angle, self.j1_graph.max_angle),
            'j2': (self.j2_graph.min_angle, self.j2_graph.max_angle),
            'j3': (self.j3_graph.min_angle, self.j3_graph.max_angle)
        }
    
    def delete_selected_point(self):
        """選択された制御点を削除"""
        for graph in [self.j1_graph, self.j2_graph, self.j3_graph]:
            if graph.selected_point:
                graph.delete_point(graph.selected_point)
                break
                
    def reset(self):
        """リセット"""
        for graph in [self.j1_graph, self.j2_graph, self.j3_graph]:
            graph.points = [ControlPoint(0, 0), ControlPoint(5000, 0)]
            graph.selected_point = None
            graph.update()
            
    def undo(self):
        """Undo"""
        for graph in [self.j1_graph, self.j2_graph, self.j3_graph]:
            graph.undo()
            
    def redo(self):
        """Redo"""
        for graph in [self.j1_graph, self.j2_graph, self.j3_graph]:
            graph.redo()