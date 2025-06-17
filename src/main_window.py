from PyQt6.QtWidgets import (QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, 
                             QMenuBar, QMenu, QSplitter, QFrame, QLabel)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction, QKeySequence

from .graph_editor import GraphEditor
from .preview_3d import Preview3D
from .timeline_controls import TimelineControls
from .project_manager import ProjectManager

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Motion Tool")
        self.setGeometry(100, 100, 1200, 800)
        
        self.project_manager = ProjectManager()
        self.setup_ui()
        self.setup_menu()
        self.setup_shortcuts()
        
    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # メインレイアウト
        main_layout = QHBoxLayout(central_widget)
        
        # スプリッター
        splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(splitter)
        
        # 左側: グラフエディタ
        graph_frame = QFrame()
        graph_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        graph_layout = QVBoxLayout(graph_frame)
        
        self.graph_editor = GraphEditor()
        graph_layout.addWidget(self.graph_editor)
        
        # タイムラインコントロール
        self.timeline_controls = TimelineControls()
        graph_layout.addWidget(self.timeline_controls)
        
        splitter.addWidget(graph_frame)
        
        # 右側: 3Dプレビュー
        preview_frame = QFrame()
        preview_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        preview_layout = QVBoxLayout(preview_frame)
        
        preview_label = QLabel("3D Preview")
        preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        preview_layout.addWidget(preview_label)
        
        self.preview_3d = Preview3D()
        preview_layout.addWidget(self.preview_3d)
        
        splitter.addWidget(preview_frame)
        
        # スプリッター比率設定
        splitter.setSizes([800, 400])
        
        # 信号接続
        self.timeline_controls.time_changed.connect(self.on_time_changed)
        self.timeline_controls.play_pause_toggled.connect(self.on_play_pause)
        self.graph_editor.motion_changed.connect(self.on_motion_changed)
        
    def setup_menu(self):
        menubar = self.menuBar()
        
        # Fileメニュー
        file_menu = menubar.addMenu("File")
        
        new_action = QAction("New", self)
        new_action.setShortcut(QKeySequence.StandardKey.New)
        new_action.triggered.connect(self.new_project)
        file_menu.addAction(new_action)
        
        open_action = QAction("Open", self)
        open_action.setShortcut(QKeySequence.StandardKey.Open)
        open_action.triggered.connect(self.open_project)
        file_menu.addAction(open_action)
        
        save_action = QAction("Save", self)
        save_action.setShortcut(QKeySequence.StandardKey.Save)
        save_action.triggered.connect(self.save_project)
        file_menu.addAction(save_action)
        
        save_as_action = QAction("Save As...", self)
        save_as_action.setShortcut(QKeySequence.StandardKey.SaveAs)
        save_as_action.triggered.connect(self.save_project_as)
        file_menu.addAction(save_as_action)
        
        file_menu.addSeparator()
        
        export_action = QAction("Export CSV...", self)
        export_action.triggered.connect(self.export_csv)
        file_menu.addAction(export_action)
        
        file_menu.addSeparator()
        
        load_model_action = QAction("Load 3D Model...", self)
        load_model_action.triggered.connect(self.load_3d_model)
        file_menu.addAction(load_model_action)
        
        # Editメニュー
        edit_menu = menubar.addMenu("Edit")
        
        undo_action = QAction("Undo", self)
        undo_action.setShortcut(QKeySequence.StandardKey.Undo)
        undo_action.triggered.connect(self.undo)
        edit_menu.addAction(undo_action)
        
        redo_action = QAction("Redo", self)
        redo_action.setShortcut(QKeySequence.StandardKey.Redo)
        redo_action.triggered.connect(self.redo)
        edit_menu.addAction(redo_action)
        
    def setup_shortcuts(self):
        # Space: 再生/停止
        from PyQt6.QtGui import QShortcut
        play_shortcut = QShortcut(Qt.Key.Key_Space, self)
        play_shortcut.activated.connect(self.timeline_controls.toggle_play_pause)
        
        # Delete: 選択点削除
        delete_shortcut = QShortcut(Qt.Key.Key_Delete, self)
        delete_shortcut.activated.connect(self.graph_editor.delete_selected_point)
        
    def on_time_changed(self, time_ms):
        """タイムライン時間変更"""
        angles = self.graph_editor.get_angles_at_time(time_ms)
        self.preview_3d.update_pose(angles)
        
    def on_play_pause(self, is_playing):
        """再生/停止切り替え"""
        if is_playing:
            self.timeline_controls.start_playback()
        else:
            self.timeline_controls.stop_playback()
            
    def on_motion_changed(self):
        """モーション変更時"""
        # 現在時刻での3Dプレビュー更新
        current_time = self.timeline_controls.get_current_time()
        angles = self.graph_editor.get_angles_at_time(current_time)
        self.preview_3d.update_pose(angles)
        
    def new_project(self):
        self.project_manager.new_project()
        self.graph_editor.reset()
        self.timeline_controls.reset()
        
    def open_project(self):
        if self.project_manager.open_project():
            data = self.project_manager.get_project_data()
            self.graph_editor.load_data(data)
            self.timeline_controls.set_duration(data.get('duration', 5000))
            
    def save_project(self):
        data = {
            'motion_data': self.graph_editor.get_motion_data(),
            'duration': self.timeline_controls.get_duration(),
            'angle_ranges': self.graph_editor.get_angle_ranges()
        }
        self.project_manager.save_project(data)
        
    def save_project_as(self):
        data = {
            'motion_data': self.graph_editor.get_motion_data(),
            'duration': self.timeline_controls.get_duration(),
            'angle_ranges': self.graph_editor.get_angle_ranges()
        }
        self.project_manager.save_project_as(data)
        
    def export_csv(self):
        data = self.graph_editor.get_motion_data()
        duration = self.timeline_controls.get_duration()
        self.project_manager.export_csv(data, duration)
        
    def load_3d_model(self):
        self.preview_3d.load_model()
        
    def undo(self):
        self.graph_editor.undo()
        
    def redo(self):
        self.graph_editor.redo()