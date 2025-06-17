import math
import numpy as np
from scipy.interpolate import CubicSpline
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QDoubleSpinBox, QCheckBox, QPushButton, QFrame,
                             QScrollArea, QSlider)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QPointF
from PyQt6.QtGui import QPainter, QPen, QBrush, QColor, QFont
from .config import config

class ControlPoint:
    def __init__(self, time_ms, angle_rad):
        self.time_ms = time_ms
        self.angle_rad = angle_rad
        self.selected = False

class AxisGraph(QWidget):
    """単一軸のグラフウィジェット"""
    
    motion_changed = pyqtSignal()
    selection_changed = pyqtSignal()
    
    def __init__(self, axis_name, color, min_angle=-math.pi/2, max_angle=math.pi/2):
        super().__init__()
        self.axis_name = axis_name
        self.color = QColor(color)
        self.min_angle = min_angle
        self.max_angle = max_angle
        self.duration_ms = 5000  # 編集可能時間
        self.points = [ControlPoint(0, 0), ControlPoint(self.duration_ms, 0)]  # 初期点
        self.selected_point = None
        self.dragging = False
        self.snap_enabled = True
        self.grid_time = 100  # ms
        
        # ズーム・スクロール
        self.zoom_factor = 1.0
        self.scroll_offset = 0.0  # time in ms
        
        # ホバー表示
        self.hover_time = None
        self.hover_angle = None
        
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
        """時間をX座標に変換（ズーム・スクロール対応）"""
        margin = 40
        visible_duration = self.duration_ms / self.zoom_factor
        relative_time = time_ms - self.scroll_offset
        return margin + (relative_time / visible_duration) * (self.width() - 2 * margin)
    
    def x_to_time(self, x):
        """X座標を時間に変換（ズーム・スクロール対応）"""
        margin = 40
        visible_duration = self.duration_ms / self.zoom_factor
        relative_time = ((x - margin) / (self.width() - 2 * margin)) * visible_duration
        return relative_time + self.scroll_offset
    
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
        
        time_ms = max(0, min(self.duration_ms, time_ms))
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
        max_time = self.points[idx+1].time_ms if idx < len(self.points)-1 else self.duration_ms
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
        
        # ホバー情報描画
        self.draw_hover_info(painter)
        
        # 軸ラベル
        self.draw_labels(painter)
    
    def draw_grid(self, painter):
        """グリッド描画"""
        pen = QPen(QColor(220, 220, 220))
        painter.setPen(pen)
        
        margin = 40
        
        # 縦線（時間グリッド）
        visible_duration = self.duration_ms / self.zoom_factor
        grid_step = int(max(100, visible_duration // 10))
        start_time = int(self.scroll_offset // grid_step) * grid_step
        end_time = int(self.scroll_offset + visible_duration)
        
        for t in range(int(start_time), end_time + grid_step, grid_step):
            if 0 <= t <= self.duration_ms:
                x = int(self.time_to_x(t))
                if 0 <= x <= self.width():
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
        visible_duration = self.duration_ms / self.zoom_factor
        draw_step = max(5, int(visible_duration // 100))
        start_time = max(0, self.scroll_offset - draw_step)
        end_time = min(self.duration_ms, self.scroll_offset + visible_duration + draw_step)
        
        prev_x = None
        prev_y = None
        
        for t in np.arange(start_time, end_time + draw_step, draw_step):
            if t > self.duration_ms:
                break
            angle = self.get_interpolated_value(t)
            x = int(self.time_to_x(t))
            y = int(self.angle_to_y(angle))
            
            if prev_x is not None and 0 <= x <= self.width():
                painter.drawLine(prev_x, prev_y, x, y)
            prev_x, prev_y = x, y
    
    def draw_points(self, painter):
        """制御点描画"""
        for point in self.points:
            x = int(self.time_to_x(point.time_ms))
            y = int(self.angle_to_y(point.angle_rad))
            
            # 可視範囲内の点のみ描画
            if 0 <= x <= self.width():
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
    
    def draw_hover_info(self, painter):
        """ホバー情報描画"""
        if self.hover_time is not None and self.hover_angle is not None:
            # ホバー位置に十字線を描画
            x = int(self.time_to_x(self.hover_time))
            y = int(self.angle_to_y(self.hover_angle))
            
            if 0 <= x <= self.width() and 0 <= y <= self.height():
                pen = QPen(QColor(255, 0, 0, 150), 1, Qt.PenStyle.DashLine)
                painter.setPen(pen)
                
                # 垂直線
                painter.drawLine(x, 0, x, self.height())
                # 水平線  
                painter.drawLine(0, y, self.width(), y)
                
                # 情報テキスト
                info_text = f"Time: {self.hover_time:.0f}ms, Angle: {self.hover_angle:.3f}rad"
                
                # テキスト背景
                font = QFont()
                font.setPointSize(9)
                painter.setFont(font)
                
                text_rect = painter.fontMetrics().boundingRect(info_text)
                text_x = min(x + 10, self.width() - text_rect.width() - 5)
                text_y = max(y - 10, text_rect.height() + 5)
                
                # 背景描画
                bg_rect = text_rect.translated(text_x, text_y - text_rect.height())
                bg_rect.adjust(-3, -2, 3, 2)
                painter.fillRect(bg_rect, QColor(255, 255, 255, 200))
                painter.setPen(QPen(Qt.GlobalColor.black))
                painter.drawRect(bg_rect)
                
                # テキスト描画
                painter.drawText(text_x, text_y, info_text)
    
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
        
        # 時間表示（可視範囲の開始と終了）
        visible_duration = self.duration_ms / self.zoom_factor
        start_time = self.scroll_offset
        end_time = min(self.duration_ms, self.scroll_offset + visible_duration)
        
        start_x = int(self.time_to_x(start_time))
        end_x = int(self.time_to_x(end_time))
        
        if start_x >= 0:
            painter.drawText(start_x - 10, self.height() - 5, str(int(start_time)))
        if end_x <= self.width():
            painter.drawText(end_x - 20, self.height() - 5, str(int(end_time)))
    
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
            self.selection_changed.emit()
            
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
        else:
            # ホバー情報更新
            mouse_time = self.x_to_time(event.position().x())
            if 0 <= mouse_time <= self.duration_ms:
                self.hover_time = mouse_time
                self.hover_angle = self.get_interpolated_value(mouse_time)
            else:
                self.hover_time = None
                self.hover_angle = None
            self.update()
    
    def mouseReleaseEvent(self, event):
        self.dragging = False
        
    def leaveEvent(self, event):
        """マウスが領域外に出た時"""
        self.hover_time = None
        self.hover_angle = None
        self.update()
        
    def set_zoom(self, zoom_factor):
        """ズーム設定"""
        self.zoom_factor = max(0.1, min(10.0, zoom_factor))
        # スクロール位置を調整して範囲内に収める
        visible_duration = self.duration_ms / self.zoom_factor
        if self.scroll_offset + visible_duration > self.duration_ms:
            self.scroll_offset = max(0, self.duration_ms - visible_duration)
        self.update()
        
    def set_scroll_offset(self, offset):
        """スクロール位置設定"""
        visible_duration = self.duration_ms / self.zoom_factor
        max_offset = max(0, self.duration_ms - visible_duration)
        self.scroll_offset = max(0, min(max_offset, offset))
        self.update()

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
        
        # Duration設定
        control_layout.addWidget(QLabel("Duration:"))
        self.duration_spinbox = QDoubleSpinBox()
        self.duration_spinbox.setRange(1000, 60000)
        self.duration_spinbox.setValue(5000)
        self.duration_spinbox.setSuffix(" ms")
        self.duration_spinbox.valueChanged.connect(self.on_duration_changed)
        control_layout.addWidget(self.duration_spinbox)
        
        # Snap設定
        self.snap_checkbox = QCheckBox("Snap to Grid")
        self.snap_checkbox.setChecked(True)
        self.snap_checkbox.toggled.connect(self.on_snap_toggled)
        control_layout.addWidget(self.snap_checkbox)
        
        # ズームコントロール
        control_layout.addWidget(QLabel("Zoom:"))
        self.zoom_slider = QSlider(Qt.Orientation.Horizontal)
        self.zoom_slider.setRange(10, 1000)  # 0.1x to 10.0x
        self.zoom_slider.setValue(100)  # 1.0x
        self.zoom_slider.setMaximumWidth(100)
        self.zoom_slider.valueChanged.connect(self.on_zoom_changed)
        control_layout.addWidget(self.zoom_slider)
        
        self.zoom_label = QLabel("1.0x")
        self.zoom_label.setMinimumWidth(40)
        control_layout.addWidget(self.zoom_label)
        
        # 選択点の値編集
        control_layout.addWidget(QLabel("Selected Point:"))
        control_layout.addWidget(QLabel("Time:"))
        self.time_spinbox = QDoubleSpinBox()
        self.time_spinbox.setRange(0, 10000)  # 初期値は大きめに設定
        self.time_spinbox.setSuffix(" ms")
        control_layout.addWidget(self.time_spinbox)
        
        control_layout.addWidget(QLabel("Angle:"))
        self.angle_spinbox = QDoubleSpinBox()
        # 初期値は最大範囲に設定（後で選択された軸に応じて動的変更）
        all_limits = config.get_all_angle_limits()
        max_range = max([max(abs(limits[0]), abs(limits[1])) for limits in all_limits.values()])
        self.angle_spinbox.setRange(-max_range, max_range)
        self.angle_spinbox.setSuffix(" rad")
        self.angle_spinbox.setDecimals(3)
        self.angle_spinbox.valueChanged.connect(self.on_angle_changed)
        control_layout.addWidget(self.angle_spinbox)
        
        # 値変更時の信号接続
        self.time_spinbox.valueChanged.connect(self.on_time_changed)
        
        control_layout.addStretch()
        layout.addWidget(control_panel)
        
        # 軸グラフ（コンフィグから角度制限を取得）
        angle_limits = config.get_all_angle_limits()
        
        self.j1_graph = AxisGraph("J1 (Yaw)", "blue", 
                                 min_angle=angle_limits['j1'][0], 
                                 max_angle=angle_limits['j1'][1])
        self.j2_graph = AxisGraph("J2 (Roll)", "green",
                                 min_angle=angle_limits['j2'][0], 
                                 max_angle=angle_limits['j2'][1]) 
        self.j3_graph = AxisGraph("J3 (Pitch)", "red",
                                 min_angle=angle_limits['j3'][0], 
                                 max_angle=angle_limits['j3'][1])
        
        for graph in [self.j1_graph, self.j2_graph, self.j3_graph]:
            graph.motion_changed.connect(self.motion_changed.emit)
            graph.selection_changed.connect(self.update_selected_point_info)
            layout.addWidget(graph)
            
        # 選択点変更の信号接続
        self.update_selected_point_info()
            
        # 横スクロールバー
        self.scroll_bar = QSlider(Qt.Orientation.Horizontal)
        self.scroll_bar.setRange(0, 0)  # 初期値
        self.scroll_bar.valueChanged.connect(self.on_scroll_changed)
        layout.addWidget(self.scroll_bar)
            
    def on_duration_changed(self, value):
        """Duration設定変更"""
        for graph in [self.j1_graph, self.j2_graph, self.j3_graph]:
            # 現在の最大時間点を調整
            max_point = max(graph.points, key=lambda p: p.time_ms)
            if max_point.time_ms > value:
                max_point.time_ms = value
            
            graph.duration_ms = value
            graph.update()
        
        # Time spinboxの範囲も更新
        self.time_spinbox.setRange(0, value)
        
        # スクロールバー範囲更新
        self.update_scroll_range()
            
    def on_snap_toggled(self, checked):
        """スナップ設定変更"""
        for graph in [self.j1_graph, self.j2_graph, self.j3_graph]:
            graph.snap_enabled = checked
            
    def on_zoom_changed(self, value):
        """ズーム変更"""
        zoom_factor = value / 100.0  # 0.1x to 10.0x
        self.zoom_label.setText(f"{zoom_factor:.1f}x")
        
        for graph in [self.j1_graph, self.j2_graph, self.j3_graph]:
            graph.set_zoom(zoom_factor)
            
        self.update_scroll_range()
        
    def on_scroll_changed(self, value):
        """スクロール変更"""
        for graph in [self.j1_graph, self.j2_graph, self.j3_graph]:
            graph.set_scroll_offset(value)
            
    def update_scroll_range(self):
        """スクロールバー範囲更新"""
        zoom_factor = self.zoom_slider.value() / 100.0
        visible_duration = self.j1_graph.duration_ms / zoom_factor
        max_offset = max(0, self.j1_graph.duration_ms - visible_duration)
        
        self.scroll_bar.setRange(0, int(max_offset))
        if max_offset <= 0:
            self.scroll_bar.setEnabled(False)
        else:
            self.scroll_bar.setEnabled(True)
            
    def update_selected_point_info(self):
        """選択点情報を更新"""
        selected_point = None
        selected_graph = None
        
        # 送信者を特定して他のグラフの選択をクリア
        sender_graph = self.sender() if hasattr(self, 'sender') and self.sender() else None
        
        for graph in [self.j1_graph, self.j2_graph, self.j3_graph]:
            if graph != sender_graph and graph.selected_point:
                graph.selected_point = None
                graph.update()
                
        for graph in [self.j1_graph, self.j2_graph, self.j3_graph]:
            if graph.selected_point:
                selected_point = graph.selected_point
                selected_graph = graph
                break
        
        if selected_point:
            self.time_spinbox.blockSignals(True)
            self.angle_spinbox.blockSignals(True)
            
            # 選択された軸に応じてangle_spinboxの範囲を設定
            if selected_graph:
                min_angle = selected_graph.min_angle
                max_angle = selected_graph.max_angle
                self.angle_spinbox.setRange(min_angle, max_angle)
            
            self.time_spinbox.setValue(selected_point.time_ms)
            self.angle_spinbox.setValue(selected_point.angle_rad)
            self.time_spinbox.setEnabled(True)
            self.angle_spinbox.setEnabled(True)
            
            self.time_spinbox.blockSignals(False)
            self.angle_spinbox.blockSignals(False)
        else:
            self.time_spinbox.setEnabled(False)
            self.angle_spinbox.setEnabled(False)
            
    def on_time_changed(self, value):
        """Time spinbox変更"""
        selected_graph = None
        selected_point = None
        
        for graph in [self.j1_graph, self.j2_graph, self.j3_graph]:
            if graph.selected_point:
                selected_graph = graph
                selected_point = graph.selected_point
                break
                
        if selected_graph and selected_point:
            selected_graph.save_state()
            selected_graph.move_point(selected_point, value, selected_point.angle_rad)
            
    def on_angle_changed(self, value):
        """Angle spinbox変更"""
        selected_graph = None
        selected_point = None
        
        for graph in [self.j1_graph, self.j2_graph, self.j3_graph]:
            if graph.selected_point:
                selected_graph = graph
                selected_point = graph.selected_point
                break
                
        if selected_graph and selected_point:
            selected_graph.save_state()
            selected_graph.move_point(selected_point, selected_point.time_ms, value)
            
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
            graph.points = [ControlPoint(0, 0), ControlPoint(graph.duration_ms, 0)]
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