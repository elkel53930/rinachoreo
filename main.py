#!/usr/bin/env python3
"""
3軸ロボットモーション作成ツール
"""

import sys
from PyQt6.QtWidgets import QApplication
from src.main_window import MainWindow

def main():
    app = QApplication(sys.argv)
    app.setApplicationName("RinaChoreo")
    app.setApplicationVersion("1.0.0")
    
    window = MainWindow()
    window.show()
    
    sys.exit(app.exec())

if __name__ == "__main__":
    main()