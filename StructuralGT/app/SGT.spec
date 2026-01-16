# -*- mode: python ; coding: utf-8 -*-

import os
import sys
import pathlib
from PyInstaller.utils.hooks import collect_data_files

block_cipher = None
is_macos = sys.platform == "darwin"
is_windows = sys.platform == "win32"

project_root = pathlib.Path(SPECPATH)
app_dir = project_root / "src"

app_name = "SGT"
icon_path = app_dir / "view" / "resources" / "icons" / (
    "StructuralGT.icns" if is_macos else
    "StructuralGT.ico" if is_windows else
    "StructuralGT.png"
)
icon_file = str(icon_path) if icon_path.exists() else None
bundle_identifier = "com.structuralgt.gui" if is_macos else None

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
    binary_ext = "*.dylib" if is_macos else ("*.dll" if is_windows else "*.so")
    pyside6_datas = collect_data_files("PySide6", includes=["**/*.qml", "**/*.qm", f"**/{binary_ext}"])
    datas.extend(pyside6_datas)
except Exception:
    pass

env_base = None
if "CONDA_PREFIX" in os.environ:
    env_base = pathlib.Path(os.environ["CONDA_PREFIX"])
elif "MAMBA_ROOT_PREFIX" in os.environ:
    env_base = pathlib.Path(os.environ["MAMBA_ROOT_PREFIX"], "envs", os.environ.get("CONDA_DEFAULT_ENV", "SGT_GUI"))

if env_base:
    import sysconfig
    import shutil
    import tempfile
    import re
    
    site_packages = pathlib.Path(sysconfig.get_path("purelib"))
    lib_ovito_dir = site_packages / "ovito"
    
    if lib_ovito_dir.exists():
        temp_ovito_dir = pathlib.Path(tempfile.mkdtemp())
        temp_ovito_package = temp_ovito_dir / "ovito"
        shutil.copytree(lib_ovito_dir, temp_ovito_package)
        
        plugins_init = temp_ovito_package / "plugins" / "__init__.py"
        if plugins_init.exists():
            content = plugins_init.read_text(encoding="utf-8")
            
            old_condition = "if 'ON' == 'OFF' or not getattr(sys, \"_ovito_embedded_mode\", False):"
            content = content.replace(old_condition, "if hasattr(sys, \"_MEIPASS\") or not getattr(sys, \"_ovito_embedded_mode\", False):")
            
            pattern = r'(\s+)__path__\[0\] \+= .*(?:Library.*bin|ovito/plugins).*'
            match = re.search(pattern, content)
            if match:
                indent = match.group(1)
                replacement = f'{indent}# Modified for PyInstaller\n{indent}import pathlib\n{indent}__path__[0] = str(pathlib.Path(__path__[0]).parent.parent / "lib" / "ovito" / "plugins")'
                content = re.sub(pattern, replacement, content)
                plugins_init.write_text(content, encoding="utf-8")
        
        datas.append((str(temp_ovito_package), "ovito"))
        print(f"[SPEC] Including ovito (patched)")

try:
    import StructuralGT
    metadata_json = pathlib.Path(StructuralGT.__file__).parent / "metadata.json"
    if metadata_json.exists():
        datas.append((str(metadata_json), "StructuralGT"))
except Exception:
    pass

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
    import glob
    
    if is_windows:
        lib_ovito_bin = env_base / "Library" / "bin"
        if lib_ovito_bin.exists():
            for pattern in ["ovito*.pyd", "ovito*.dll", "embree*.dll", "anari*.dll", "ospray*.dll", "OpenImageDenoise*.dll"]:
                binaries.extend([(p, "lib/ovito/plugins") for p in glob.glob(str(lib_ovito_bin / pattern))])
    else:
        lib_ovito_dir = env_base / "lib" / "ovito"
        if lib_ovito_dir.exists():
            for ext in (["*.so", "*.dylib"] if is_macos else ["*.so"]):
                for binary_path in glob.glob(str(lib_ovito_dir / "**" / ext), recursive=True):
                    rel_path = pathlib.Path(binary_path).relative_to(lib_ovito_dir)
                    target = f"lib/ovito/{rel_path.parent}" if str(rel_path.parent) != "." else "lib/ovito"
                    binaries.append((binary_path, target))

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
) if is_macos else coll
