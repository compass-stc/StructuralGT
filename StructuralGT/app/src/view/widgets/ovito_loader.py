"""OVITO loader for PyInstaller environment."""

import sys
import os
import pathlib
import types
import importlib.util
import importlib.machinery

# Set OVITO GUI mode environment variable BEFORE importing ovito
os.environ["OVITO_GUI_MODE"] = "1"

if hasattr(sys, "_MEIPASS"):
    _MEIPASS = sys._MEIPASS

    correct_plugins_path = None
    for path in [
        pathlib.Path(_MEIPASS, "lib", "ovito", "plugins"),
        pathlib.Path(_MEIPASS, "ovito", "plugins"),
    ]:
        if path.exists() and (path / "ovito_bindings.so").exists():
            correct_plugins_path = str(path)
            break

    if not correct_plugins_path:
        raise RuntimeError(
            f"Could not find ovito plugins directory in {_MEIPASS}"
        )

    import ovito

    # Set up ovito.plugins module
    if not hasattr(ovito, "plugins"):
        plugins_module = types.ModuleType("ovito.plugins")
        plugins_module.__package__ = "ovito.plugins"
        sys.modules["ovito.plugins"] = plugins_module
        ovito.plugins = plugins_module
    else:
        plugins_module = ovito.plugins

    # Set correct __path__ for PyInstaller
    plugins_module.__path__ = [correct_plugins_path]

    # Load ovito_bindings.so directly
    binding_file = pathlib.Path(correct_plugins_path) / "ovito_bindings.so"
    if binding_file.exists():
        try:
            loader = importlib.machinery.ExtensionFileLoader(
                "ovito.plugins.ovito_bindings", str(binding_file)
            )
            spec = importlib.machinery.ModuleSpec(
                "ovito.plugins.ovito_bindings",
                loader,
                origin=str(binding_file),
            )

            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                module.__package__ = "ovito.plugins"
                sys.modules["ovito.plugins.ovito_bindings"] = module
                spec.loader.exec_module(module)
                plugins_module.ovito_bindings = module
        except Exception:
            pass

    # Import function injection modules
    if hasattr(ovito, "gui"):
        try:
            # Triggers create_qwidget injection
            import ovito.gui._create_qwidget
        except ImportError:
            pass

        try:
            # Triggers import_file injection
            import ovito.io._import_file_func
        except ImportError:
            pass

    # Ensure scene module is fully initialized
    try:
        import ovito.scene

        _ = ovito.scene  # Force initialization
    except Exception:
        pass

    # Ensure vis module is fully initialized
    try:
        import ovito.vis

        # Trigger zoom_all() method injection
        import ovito.vis._viewport

        _ = ovito.vis.Viewport
    except Exception:
        pass

else:
    import ovito

# Export ovito module
__all__ = ["ovito"]
