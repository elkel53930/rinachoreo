import os
import math
import yaml

class Config:
    """rinachoreo設定ファイル管理クラス"""
    
    def __init__(self):
        self.config_path = "config.yaml"
        self.config_data = None
        self.load_config()
    
    def load_config(self):
        """設定ファイルを読み込み"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    self.config_data = yaml.safe_load(f)
                print(f"Config loaded from {self.config_path}")
            else:
                print(f"Config file {self.config_path} not found, using defaults")
                self.config_data = self.get_default_config()
        except Exception as e:
            print(f"Error loading config: {e}, using defaults")
            self.config_data = self.get_default_config()
    
    def get_default_config(self):
        """デフォルト設定を返す"""
        return {
            'angle_limits': {
                'j1_yaw': {
                    'min': -math.pi/2,
                    'max': math.pi/2
                },
                'j2_roll': {
                    'min': -math.pi/2,
                    'max': math.pi/2
                },
                'j3_pitch': {
                    'min': -math.pi/2,
                    'max': math.pi/2
                }
            }
        }
    
    def get_angle_limits(self, axis):
        """指定軸の角度制限を取得"""
        try:
            limits = self.config_data['angle_limits'][axis]
            return limits['min'], limits['max']
        except (KeyError, TypeError):
            print(f"Warning: angle limits for {axis} not found, using default ±π/2")
            return -math.pi/2, math.pi/2
    
    def get_all_angle_limits(self):
        """全軸の角度制限を取得"""
        return {
            'j1': self.get_angle_limits('j1_yaw'),
            'j2': self.get_angle_limits('j2_roll'),
            'j3': self.get_angle_limits('j3_pitch')
        }

# グローバル設定インスタンス
config = Config()