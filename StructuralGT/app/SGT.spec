# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for SGT (macOS, Windows, Linux)
Optimized for cross-platform builds with OVITO support
"""

import os
import sys
import pathlib
from PyInstaller.utils.hooks import collect_data_files

# Block cipher for encryption
block_cipher = None

# Detect platform
is_macos = sys.platform == "darwin"
is_windows = sys.platform == "win32"

project_root = pathlib.Path(SPECPATH)
app_dir = project_root / "src"

# Platform-specific settings
app_name = "SGT"
if is_macos:
    icon_path = app_dir / "view" / "resources" / "icons" / "StructuralGT.icns"
    bundle_identifier = "com.structuralgt.gui"
elif is_windows:
    icon_path = app_dir / "view" / "resources" / "icons" / "StructuralGT.ico"
    bundle_identifier = None
else:
    icon_path = app_dir / "view" / "resources" / "icons" / "StructuralGT.png"
    bundle_identifier = None

icon_file = str(icon_path) if icon_path.exists() else None

datas = [
    (str(app_dir / "settings.json"), "src"),
    (str(app_dir / "view" / "resources" / "resources.qrc"), "src/view/resources"),
    (
        str(app_dir / "view" / "resources" / "style" / "custom_styles.qss"),
        "src/view/resources/style",
    ),
    (str(app_dir / "view" / "resources" / "icons"), "src/view/resources/icons"),
]

try:
    if is_macos:
        pyside6_includes = ["**/*.qml", "**/*.qm", "**/*.dylib"]
    elif is_windows:
        pyside6_includes = ["**/*.qml", "**/*.qm", "**/*.dll"]
    else:
        pyside6_includes = ["**/*.qml", "**/*.qm", "**/*.so"]
    
    pyside6_datas = collect_data_files("PySide6", includes=pyside6_includes)
    datas.extend(pyside6_datas)
except Exception:
    pass

env_base = None
if "CONDA_PREFIX" in os.environ:
    env_base = pathlib.Path(os.environ["CONDA_PREFIX"])
elif "MAMBA_ROOT_PREFIX" in os.environ:
    mamba_root = pathlib.Path(os.environ["MAMBA_ROOT_PREFIX"])
    env_name = os.environ.get("CONDA_DEFAULT_ENV", "SGT_GUI")
    env_base = pathlib.Path(mamba_root, "envs", env_name)
    if is_windows:
        ovito_check_path = pathlib.Path(env_base, "Library", "ovito")
    else:
        ovito_check_path = pathlib.Path(env_base, "lib", "ovito")
    if not ovito_check_path.exists():
        env_base = pathlib.Path(mamba_root, "envs", "SGT_GUI")

if env_base:
    if is_windows:
        lib_ovito_dir = pathlib.Path(env_base, "Library", "ovito")
    else:
        lib_ovito_dir = pathlib.Path(env_base, "lib", "ovito")
    
    if lib_ovito_dir.exists():
        datas.append((lib_ovito_dir, "lib/ovito"))
        print(f"[SPEC] Including entire lib/ovito directory from: {lib_ovito_dir}")
    else:
        print(f"[SPEC] WARNING: lib/ovito directory not found at {lib_ovito_dir}")
else:
    print(
        f"[SPEC] WARNING: Could not determine conda/mamba environment base for OVITO"
    )

# Collect StructuralGT metadata.json
try:
    import StructuralGT

    structuralgt_path = pathlib.Path(StructuralGT.__file__).parent
    metadata_json = pathlib.Path(structuralgt_path, "metadata.json")
    if metadata_json.exists():
        datas.append((metadata_json, "StructuralGT"))
except Exception:
    pass

# Hidden imports (modules that PyInstaller might miss)
hiddenimports = [
    # PySide6
    "PySide6.QtCore",
    "PySide6.QtGui",
    "PySide6.QtWidgets",
    "PySide6.QtOpenGL",
    "PySide6.QtOpenGLWidgets",
    # StructuralGT
    "StructuralGT",
    "StructuralGT.networks",
    "StructuralGT.electronic",
    "StructuralGT.geometric",
    "StructuralGT.structural",
    # OVITO
    "ovito",
    "ovito.gui",
    "ovito.vis",
    "ovito.io",
    "ovito.scene",
    "ovito.data",
    "ovito.modifiers",
    "ovito.pipeline",
    "ovito.qt_compat",
    "ovito.plugins",
    "ovito.plugins.ovito_bindings",
    "ovito.io._import_file_func",
    "ovito.gui._create_qwidget",
    "ovito.vis._viewport",
    # Other dependencies
    "numpy",
    "pandas",
    "cv2",
    "matplotlib",
    "matplotlib.pyplot",
    "scipy",
    "skimage",
    "networkx",
    "gsd",
    "igraph",
    "freud",
    "qdarktheme",
    "pyqtdarktheme",
    # IPython (required by StructuralGT)
    "IPython",
    "IPython.display",
]

binaries = []

if env_base:
    if is_windows:
        lib_ovito_dir = pathlib.Path(env_base, "Library", "ovito")
    else:
        lib_ovito_dir = pathlib.Path(env_base, "lib", "ovito")
    
    if lib_ovito_dir.exists():
        import glob

        lib_ovito_str = str(lib_ovito_dir)
        if is_macos:
            binary_extensions = ["*.so", "*.dylib"]
        elif is_windows:
            binary_extensions = ["*.dll"]
        else:
            binary_extensions = ["*.so"]
        
        for ext in binary_extensions:
            pattern = os.path.join(lib_ovito_str, "**", ext)
            for binary_path in glob.glob(pattern, recursive=True):
                binary_path_obj = pathlib.Path(binary_path)
                rel_path = binary_path_obj.relative_to(lib_ovito_dir)
                target_dir = rel_path.parent
                if str(target_dir) == ".":
                    target_path = "lib/ovito"
                else:
                    target_path = os.path.join("lib", "ovito", str(target_dir)).replace(
                        os.sep, "/"
                    )
                binaries.append((binary_path, target_path))
                print(
                    f"[SPEC]   Including binary: {binary_path_obj.name} -> {target_path}"
                )

# Analysis phase
a = Analysis(
    [str(app_dir / "main.py")],
    pathex=[str(app_dir)],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "tkinter",
        "matplotlib.tests",
        "numpy.tests",
        "pandas.tests",
        "scipy.tests",
        "jupyter",
        "notebook",
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=True,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name=app_name,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=icon_file,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name=app_name,
)

if is_macos:
    app = BUNDLE(
        coll,
        name=f"{app_name}.app",
        icon=icon_file,
        bundle_identifier=bundle_identifier,
        info_plist={
            "NSPrincipalClass": "NSApplication",
            "NSHighResolutionCapable": "True",
            "CFBundleShortVersionString": "1.0.0",
            "CFBundleVersion": "1.0.0",
            "NSHumanReadableCopyright": "Copyright © 2025",
            "LSMinimumSystemVersion": "10.13",
        },
    )
else:
    app = coll
