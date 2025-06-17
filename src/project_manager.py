import yaml
import csv
import json
from PyQt6.QtWidgets import QFileDialog, QMessageBox
from PyQt6.QtCore import QObject
import os

class ProjectManager(QObject):
    """プロジェクト管理クラス"""
    
    def __init__(self):
        super().__init__()
        self.current_file = None
        self.project_data = {}
        
    def new_project(self):
        """新規プロジェクト作成"""
        self.current_file = None
        self.project_data = {
            'motion_data': {
                'j1': [(0, 0), (5000, 0)],
                'j2': [(0, 0), (5000, 0)],
                'j3': [(0, 0), (5000, 0)]
            },
            'duration': 5000,
            'angle_ranges': {
                'j1': (-1.5708, 1.5708),  # ±π/2
                'j2': (-1.5708, 1.5708),
                'j3': (-1.5708, 1.5708)
            },
            'model_path': None
        }
        
    def open_project(self):
        """プロジェクト読み込み"""
        file_dialog = QFileDialog()
        file_path, _ = file_dialog.getOpenFileName(
            None,
            "Open Project",
            "",
            "YAML Files (*.yaml *.yml);;JSON Files (*.json);;All Files (*)"
        )
        
        if file_path:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    if file_path.lower().endswith(('.yaml', '.yml')):
                        self.project_data = yaml.safe_load(f)
                    else:
                        self.project_data = json.load(f)
                        
                self.current_file = file_path
                return True
                
            except Exception as e:
                QMessageBox.critical(
                    None,
                    "Open Error",
                    f"Failed to open project file:\n{str(e)}"
                )
                return False
                
        return False
        
    def save_project(self, data):
        """プロジェクト保存"""
        if self.current_file:
            self._save_to_file(self.current_file, data)
        else:
            self.save_project_as(data)
            
    def save_project_as(self, data):
        """名前を付けてプロジェクト保存"""
        file_dialog = QFileDialog()
        file_path, _ = file_dialog.getSaveFileName(
            None,
            "Save Project As",
            "project.yaml",
            "YAML Files (*.yaml *.yml);;JSON Files (*.json);;All Files (*)"
        )
        
        if file_path:
            if self._save_to_file(file_path, data):
                self.current_file = file_path
                
    def _save_to_file(self, file_path, data):
        """ファイルに保存"""
        try:
            self.project_data = data
            
            with open(file_path, 'w', encoding='utf-8') as f:
                if file_path.lower().endswith(('.yaml', '.yml')):
                    yaml.dump(data, f, default_flow_style=False, allow_unicode=True)
                else:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                    
            return True
            
        except Exception as e:
            QMessageBox.critical(
                None,
                "Save Error", 
                f"Failed to save project file:\n{str(e)}"
            )
            return False
            
    def export_csv(self, motion_data, duration):
        """CSV出力"""
        file_dialog = QFileDialog()
        file_path, _ = file_dialog.getSaveFileName(
            None,
            "Export CSV",
            "motion.csv",
            "CSV Files (*.csv);;All Files (*)"
        )
        
        if file_path:
            try:
                self._generate_csv(file_path, motion_data, duration)
                QMessageBox.information(
                    None,
                    "Export Complete",
                    f"Motion data exported to:\n{file_path}"
                )
                
            except Exception as e:
                QMessageBox.critical(
                    None,
                    "Export Error",
                    f"Failed to export CSV file:\n{str(e)}"
                )
                
    def _generate_csv(self, file_path, motion_data, duration):
        """CSV生成"""
        # 補間関数（線形補間）
        def interpolate_points(points, time_ms):
            if not points:
                return 0.0
                
            # 時間でソート
            points = sorted(points, key=lambda p: p[0])
            
            if time_ms <= points[0][0]:
                return points[0][1]
            if time_ms >= points[-1][0]:
                return points[-1][1]
                
            # 線形補間
            for i in range(len(points) - 1):
                t1, a1 = points[i]
                t2, a2 = points[i + 1]
                
                if t1 <= time_ms <= t2:
                    if t2 - t1 == 0:
                        return a1
                    ratio = (time_ms - t1) / (t2 - t1)
                    return a1 + ratio * (a2 - a1)
                    
            return 0.0
            
        # CSVファイル生成
        with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            
            # ヘッダー
            writer.writerow(['time(ms)', 'J1(rad)', 'J2(rad)', 'J3(rad)'])
            
            # データ（20ms間隔）
            for time_ms in range(0, int(duration) + 1, 20):
                j1_angle = interpolate_points(motion_data.get('j1', []), time_ms)
                j2_angle = interpolate_points(motion_data.get('j2', []), time_ms)
                j3_angle = interpolate_points(motion_data.get('j3', []), time_ms)
                
                writer.writerow([
                    time_ms,
                    f"{j1_angle:.6f}",
                    f"{j2_angle:.6f}",
                    f"{j3_angle:.6f}"
                ])
                
    def get_project_data(self):
        """プロジェクトデータ取得"""
        return self.project_data
        
    def get_current_file(self):
        """現在のファイルパス取得"""
        return self.current_file