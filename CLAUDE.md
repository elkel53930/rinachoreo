# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a 3-axis robot motion editing tool (`rinachoreo`) that allows users to create and edit robot joint angle trajectories through an intuitive GUI. The tool provides:

- Graph-based motion editing for 3 axes (J1-Yaw, J2-Roll, J3-Pitch)
- 3D preview with GLTF/GLB model support
- Timeline playback with speed control
- CSV export with 20ms sampling intervals
- Project save/load functionality

## Development Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run the application
python main.py

# Run with Python module
python -m src.main_window
```

## Architecture Requirements

### Core Components
- **Motion Editor** (`src/graph_editor.py`): Graph-based interface for each axis with spline interpolation
- **3D Renderer** (`src/preview_3d.py`): OpenGL-based 3D visualization with GLTF/GLB support
- **Timeline System** (`src/timeline_controls.py`): Playback controls with variable speed (0.1x - 3.0x)
- **Export System** (`src/project_manager.py`): CSV generation and YAML/JSON project files
- **Main Window** (`src/main_window.py`): Application coordination and UI layout

### Technical Specifications
- Target: Ubuntu 22.04 desktop or local web application
- Joint angle ranges: ±90° (-π/2 to +π/2) per axis, user configurable
- Color coding: J1=Blue, J2=Green, J3=Red
- Output format: `time(ms), J1(rad), J2(rad), J3(rad)`
- Future extensibility: ZeroMQ streaming support

### Key Interactions
- Drag: Move control points
- Double-click: Add control points
- Right-click: Delete control points
- Snap to grid: Optional time grid alignment
- Keyboard shortcuts: Ctrl+Z/Y (undo/redo), Ctrl+S (save), Delete, Space (play/pause)

### UI Layout Reference
See `app_image.png` for the intended interface layout with vertically stacked graphs and 3D preview panel.