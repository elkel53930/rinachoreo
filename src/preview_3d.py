import math
import numpy as np
from OpenGL.GL import *
from OpenGL.GLU import *
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QFileDialog, QMessageBox
from PyQt6.QtOpenGLWidgets import QOpenGLWidget
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QMatrix4x4, QVector3D, QQuaternion
import json

try:
    from pygltflib import GLTF2
    GLTF_AVAILABLE = True
except ImportError:
    GLTF_AVAILABLE = False

class OpenGLWidget(QOpenGLWidget):
    """OpenGL描画ウィジェット"""
    
    def __init__(self):
        super().__init__()
        self.angles = {'j1': 0, 'j2': 0, 'j3': 0}  # radians
        self.camera_distance = 5.0
        self.camera_rotation_x = 20.0
        self.camera_rotation_y = 45.0
        self.last_mouse_pos = None
        self.model_loaded = True
        
        # デフォルトの立方体データ
        self.model_vertices = np.array([
            [-0.5, -0.5, -0.5], [0.5, -0.5, -0.5], [0.5, 0.5, -0.5], [-0.5, 0.5, -0.5],
            [-0.5, -0.5, 0.5], [0.5, -0.5, 0.5], [0.5, 0.5, 0.5], [-0.5, 0.5, 0.5]
        ], dtype=np.float32)
        
        self.model_faces = np.array([
            [4, 5, 6], [4, 6, 7], [1, 0, 3], [1, 3, 2],
            [0, 4, 7], [0, 7, 3], [5, 1, 2], [5, 2, 6],
            [3, 7, 6], [3, 6, 2], [0, 1, 5], [0, 5, 4]
        ], dtype=np.uint32)
        
        # GLTF model data
        self.gltf_meshes = []  # 複数のメッシュを格納
        
        # デフォルトモデルとしてboard.glbを読み込み
        try:
            board_path = "board.glb"
            if self.load_gltf_model(board_path):
                print(f"Loaded default model: {board_path}")
            else:
                print("Failed to load board.glb, using default cube")
        except Exception as e:
            print(f"Error loading default model: {e}")
        
        self.setMinimumSize(400, 300)
        
    def initializeGL(self):
        """OpenGL初期化"""
        glEnable(GL_DEPTH_TEST)
        glEnable(GL_LIGHTING)
        glEnable(GL_LIGHT0)
        
        # 背景色設定
        glClearColor(0.9, 0.9, 0.9, 1.0)
        
        # ライトの設定
        light_pos = [2.0, 2.0, 3.0, 1.0]
        light_ambient = [0.3, 0.3, 0.3, 1.0]
        light_diffuse = [0.8, 0.8, 0.8, 1.0]
        light_specular = [1.0, 1.0, 1.0, 1.0]
        
        glLightfv(GL_LIGHT0, GL_POSITION, light_pos)
        glLightfv(GL_LIGHT0, GL_AMBIENT, light_ambient)
        glLightfv(GL_LIGHT0, GL_DIFFUSE, light_diffuse)
        glLightfv(GL_LIGHT0, GL_SPECULAR, light_specular)
        
        # マテリアル設定
        material_ambient = [0.2, 0.2, 0.8, 1.0]
        material_diffuse = [0.3, 0.3, 0.9, 1.0]
        material_specular = [1.0, 1.0, 1.0, 1.0]
        material_shininess = [50.0]
        
        glMaterialfv(GL_FRONT, GL_AMBIENT, material_ambient)
        glMaterialfv(GL_FRONT, GL_DIFFUSE, material_diffuse)
        glMaterialfv(GL_FRONT, GL_SPECULAR, material_specular)
        glMaterialfv(GL_FRONT, GL_SHININESS, material_shininess)

    def resizeGL(self, width, height):
        """リサイズ処理"""
        if height == 0:
            height = 1
        
        glViewport(0, 0, width, height)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        
        aspect = width / height
        gluPerspective(45.0, aspect, 0.1, 100.0)
        
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()

    def paintGL(self):
        """描画処理"""
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()
        
        # カメラ位置設定
        x = self.camera_distance * math.sin(math.radians(self.camera_rotation_y)) * math.cos(math.radians(self.camera_rotation_x))
        y = self.camera_distance * math.sin(math.radians(self.camera_rotation_x))
        z = self.camera_distance * math.cos(math.radians(self.camera_rotation_y)) * math.cos(math.radians(self.camera_rotation_x))
        
        gluLookAt(x, y, z, 0, 0, 0, 0, 1, 0)
        
        # 座標軸描画
        self.draw_axes()
        
        # ロボット姿勢の適用
        glPushMatrix()
        
        # J1 (Yaw) - Y軸回転
        glRotatef(math.degrees(self.angles['j1']), 0, 1, 0)
        
        # J2 (Roll) - X軸回転
        glRotatef(math.degrees(self.angles['j2']), 1, 0, 0)
        
        # J3 (Pitch) - Z軸回転
        glRotatef(math.degrees(self.angles['j3']), 0, 0, 1)
        
        # board.glbの場合は+90度Roll補正を適用
        if self.gltf_meshes:
            glRotatef(90.0, 1, 0, 0)  # board.glbの-90度回転を補正
        
        # モデル描画
        if self.gltf_meshes:
            self.draw_gltf_model()
        else:
            self.draw_default_cube()
        
        glPopMatrix()
    
    def draw_axes(self):
        """座標軸描画"""
        glDisable(GL_LIGHTING)
        glBegin(GL_LINES)
        
        # X軸（赤）
        glColor3f(1.0, 0.0, 0.0)
        glVertex3f(0.0, 0.0, 0.0)
        glVertex3f(1.0, 0.0, 0.0)
        
        # Y軸（緑）
        glColor3f(0.0, 1.0, 0.0)
        glVertex3f(0.0, 0.0, 0.0)
        glVertex3f(0.0, 1.0, 0.0)
        
        # Z軸（青）
        glColor3f(0.0, 0.0, 1.0)
        glVertex3f(0.0, 0.0, 0.0)
        glVertex3f(0.0, 0.0, 1.0)
        
        glEnd()
        glEnable(GL_LIGHTING)
    
    def draw_default_cube(self):
        """デフォルト立方体描画"""
        glBegin(GL_TRIANGLES)
        
        for face in self.model_faces:
            # 面の法線計算
            v0 = self.model_vertices[face[0]]
            v1 = self.model_vertices[face[1]]
            v2 = self.model_vertices[face[2]]
            
            edge1 = v1 - v0
            edge2 = v2 - v0
            normal = np.cross(edge1, edge2)
            normal = normal / np.linalg.norm(normal)
            
            glNormal3f(normal[0], normal[1], normal[2])
            
            for vertex_idx in face:
                vertex = self.model_vertices[vertex_idx]
                glVertex3f(vertex[0], vertex[1], vertex[2])
        
        glEnd()
    
    def draw_gltf_model(self):
        """GLTFモデル描画"""
        for mesh_data in self.gltf_meshes:
            vertices = mesh_data.get('vertices')
            faces = mesh_data.get('faces')
            normals = mesh_data.get('normals')
            colors = mesh_data.get('colors')
            material = mesh_data.get('material', {})
            
            if vertices is None or faces is None:
                continue
            
            # マテリアル設定
            if material:
                base_color = material.get('baseColorFactor', [0.8, 0.8, 0.8, 1.0])
                glMaterialfv(GL_FRONT, GL_AMBIENT, [base_color[0] * 0.3, base_color[1] * 0.3, base_color[2] * 0.3, base_color[3]])
                glMaterialfv(GL_FRONT, GL_DIFFUSE, base_color)
            
            glBegin(GL_TRIANGLES)
            
            for i, face in enumerate(faces):
                # 法線の設定
                if normals is not None:
                    for j, vertex_idx in enumerate(face):
                        if vertex_idx < len(normals):
                            normal = normals[vertex_idx]
                            glNormal3f(normal[0], normal[1], normal[2])
                        
                        # 頂点カラーの設定
                        if colors is not None and vertex_idx < len(colors):
                            color = colors[vertex_idx]
                            if len(color) >= 3:
                                glColor3f(color[0], color[1], color[2])
                        
                        # 頂点座標
                        if vertex_idx < len(vertices):
                            vertex = vertices[vertex_idx]
                            glVertex3f(vertex[0], vertex[1], vertex[2])
                else:
                    # 法線がない場合は面の法線を計算
                    if len(face) >= 3:
                        v0 = vertices[face[0]]
                        v1 = vertices[face[1]]
                        v2 = vertices[face[2]]
                        
                        edge1 = v1 - v0
                        edge2 = v2 - v0
                        normal = np.cross(edge1, edge2)
                        norm_length = np.linalg.norm(normal)
                        if norm_length > 0:
                            normal = normal / norm_length
                            glNormal3f(normal[0], normal[1], normal[2])
                    
                    for vertex_idx in face:
                        # 頂点カラーの設定
                        if colors is not None and vertex_idx < len(colors):
                            color = colors[vertex_idx]
                            if len(color) >= 3:
                                glColor3f(color[0], color[1], color[2])
                        
                        # 頂点座標
                        if vertex_idx < len(vertices):
                            vertex = vertices[vertex_idx]
                            glVertex3f(vertex[0], vertex[1], vertex[2])
            
            glEnd()

    def load_gltf_model(self, filepath):
        """GLTFモデル読み込み"""
        if not GLTF_AVAILABLE:
            return False
        
        try:
            gltf = GLTF2().load(filepath)
            self.gltf_meshes = []
            
            # すべてのメッシュを処理
            for mesh_idx, mesh in enumerate(gltf.meshes):
                for primitive_idx, primitive in enumerate(mesh.primitives):
                    mesh_data = {}
                    
                    # 頂点データの取得
                    if primitive.attributes.POSITION is not None:
                        vertices = self._get_accessor_data(gltf, primitive.attributes.POSITION, filepath)
                        mesh_data['vertices'] = vertices.reshape(-1, 3)
                    
                    # インデックスデータの取得
                    if primitive.indices is not None:
                        indices_data = self._get_accessor_data(gltf, primitive.indices, filepath)
                        mesh_data['faces'] = indices_data.reshape(-1, 3)
                    
                    # 法線データの取得
                    if hasattr(primitive.attributes, 'NORMAL') and primitive.attributes.NORMAL is not None:
                        normals = self._get_accessor_data(gltf, primitive.attributes.NORMAL, filepath)
                        mesh_data['normals'] = normals.reshape(-1, 3)
                    
                    # 頂点カラーの取得
                    if hasattr(primitive.attributes, 'COLOR_0') and primitive.attributes.COLOR_0 is not None:
                        colors = self._get_accessor_data(gltf, primitive.attributes.COLOR_0, filepath)
                        # カラーデータの形状を確認
                        color_accessor = gltf.accessors[primitive.attributes.COLOR_0]
                        if color_accessor.type == 'VEC3':
                            mesh_data['colors'] = colors.reshape(-1, 3)
                        elif color_accessor.type == 'VEC4':
                            mesh_data['colors'] = colors.reshape(-1, 4)
                    
                    # マテリアル情報の取得
                    if primitive.material is not None and gltf.materials:
                        material = gltf.materials[primitive.material]
                        material_data = {}
                        
                        if hasattr(material, 'pbrMetallicRoughness') and material.pbrMetallicRoughness:
                            pbr = material.pbrMetallicRoughness
                            if hasattr(pbr, 'baseColorFactor') and pbr.baseColorFactor:
                                material_data['baseColorFactor'] = pbr.baseColorFactor
                            if hasattr(pbr, 'metallicFactor') and pbr.metallicFactor is not None:
                                material_data['metallicFactor'] = pbr.metallicFactor
                            if hasattr(pbr, 'roughnessFactor') and pbr.roughnessFactor is not None:
                                material_data['roughnessFactor'] = pbr.roughnessFactor
                        
                        mesh_data['material'] = material_data
                    
                    if mesh_data.get('vertices') is not None:
                        self.gltf_meshes.append(mesh_data)
            
            print(f"Loaded {len(self.gltf_meshes)} mesh primitives from GLB file")
            return True
            
        except Exception as e:
            print(f"GLTF loading error: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _get_accessor_data(self, gltf, accessor_index, filepath):
        """アクセサからデータを取得"""
        accessor = gltf.accessors[accessor_index]
        buffer_view = gltf.bufferViews[accessor.bufferView]
        buffer = gltf.buffers[buffer_view.buffer]
        
        # GLBファイルからバイナリデータを取得
        try:
            with open(filepath, 'rb') as f:
                # GLBファイルのヘッダーをスキップしてバイナリデータを取得
                f.seek(0)
                header = f.read(12)  # GLBヘッダー
                if header[:4] == b'glTF':
                    # JSON長を読み取り
                    json_length = int.from_bytes(f.read(4), 'little')
                    json_type = f.read(4)
                    f.seek(json_length, 1)  # JSONセクションをスキップ
                    
                    # バイナリチャンクヘッダーを読み取り
                    chunk_length = int.from_bytes(f.read(4), 'little')
                    chunk_type = f.read(4)
                    
                    if chunk_type == b'BIN\x00':
                        binary_data = f.read(chunk_length)
                    else:
                        raise ValueError("Invalid GLB file format")
                else:
                    raise ValueError("Not a valid GLB file")
        except Exception as e:
            print(f"Error reading binary data: {e}")
            return np.array([])
        
        # バイトオフセットとバイト長を考慮してデータを切り出し
        start_offset = buffer_view.byteOffset + (accessor.byteOffset or 0)
        end_offset = start_offset + buffer_view.byteLength
        
        if end_offset > len(binary_data):
            print(f"Buffer overflow: trying to read {end_offset} bytes from {len(binary_data)} byte buffer")
            return np.array([])
            
        data_slice = binary_data[start_offset:end_offset]
        
        # データタイプに応じて配列に変換
        if accessor.componentType == 5120:  # BYTE
            return np.frombuffer(data_slice, dtype=np.int8)
        elif accessor.componentType == 5121:  # UNSIGNED_BYTE
            return np.frombuffer(data_slice, dtype=np.uint8)
        elif accessor.componentType == 5122:  # SHORT
            return np.frombuffer(data_slice, dtype=np.int16)
        elif accessor.componentType == 5123:  # UNSIGNED_SHORT
            return np.frombuffer(data_slice, dtype=np.uint16)
        elif accessor.componentType == 5125:  # UNSIGNED_INT
            return np.frombuffer(data_slice, dtype=np.uint32)
        elif accessor.componentType == 5126:  # FLOAT
            return np.frombuffer(data_slice, dtype=np.float32)
        else:
            raise ValueError(f"Unsupported component type: {accessor.componentType}")
    def update_pose(self, angles):
        """姿勢更新"""
        self.angles = angles
        self.update()
        
    def mousePressEvent(self, event):
        """マウス押下"""
        self.last_mouse_pos = event.position()
        
    def mouseMoveEvent(self, event):
        """マウス移動"""
        if self.last_mouse_pos:
            dx = event.position().x() - self.last_mouse_pos.x()
            dy = event.position().y() - self.last_mouse_pos.y()
            
            if event.buttons() & Qt.MouseButton.LeftButton:
                self.camera_rotation_y += dx * 0.5
                self.camera_rotation_x += dy * 0.5
                self.update()
                
            self.last_mouse_pos = event.position()
            
    def wheelEvent(self, event):
        """マウスホイール"""
        delta = event.angleDelta().y()
        self.camera_distance *= (0.9 if delta > 0 else 1.1)
        self.update()

class Preview3D(QWidget):
    """3Dプレビューウィジェット"""
    
    def __init__(self):
        super().__init__()
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # モデル名表示のみ
        self.model_label = QLabel("Model: board.glb")
        self.model_label.setMaximumHeight(20)
        font = self.model_label.font()
        font.setPointSize(8)
        self.model_label.setFont(font)
        layout.addWidget(self.model_label)
        
        # OpenGLウィジェット
        self.opengl_widget = OpenGLWidget()
        layout.addWidget(self.opengl_widget)
        
        # 角度表示
        info_layout = QHBoxLayout()
        self.angle_label = QLabel("J1: 0.00, J2: 0.00, J3: 0.00")
        info_layout.addWidget(self.angle_label)
        info_layout.addStretch()
        layout.addLayout(info_layout)
        
    def load_model(self):
        """3Dモデル読み込み"""
        file_dialog = QFileDialog()
        file_path, _ = file_dialog.getOpenFileName(
            self, 
            "Load 3D Model", 
            "", 
            "GLTF Files (*.gltf *.glb);;All Files (*)"
        )
        
        if file_path:
            if self.opengl_widget.load_gltf_model(file_path):
                self.model_label.setText(f"Model: {file_path.split('/')[-1]}")
                self.opengl_widget.update()
            else:
                QMessageBox.warning(
                    self, 
                    "Load Error", 
                    "Failed to load 3D model. Using default model."
                )
                
    def update_pose(self, angles):
        """姿勢更新"""
        self.opengl_widget.update_pose(angles)
        
        # 角度表示更新
        j1_deg = math.degrees(angles.get('j1', 0))
        j2_deg = math.degrees(angles.get('j2', 0))
        j3_deg = math.degrees(angles.get('j3', 0))
        
        self.angle_label.setText(
            f"J1: {j1_deg:.1f}°, J2: {j2_deg:.1f}°, J3: {j3_deg:.1f}°"
        )