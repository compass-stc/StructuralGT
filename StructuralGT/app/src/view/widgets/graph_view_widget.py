"""Graph view widget for StructuralGT GUI."""

from PySide6.QtWidgets import QWidget, QVBoxLayout, QSizePolicy
import pathlib
from typing import Optional

# Import OVITO using the loader module
from view.widgets.ovito_loader import ovito as ov
from service.main_controller import MainController


class GraphViewWidget(QWidget):
    """Graph view widget for StructuralGT GUI."""

    def __init__(self, parent, controller: Optional[MainController] = None):
        """Initialize the graph view widget."""
        super().__init__(parent)
        self.controller = controller

        self.setVisible(False)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # Create a viewport for rendering the graph
        self.viewport = ov.vis.Viewport(type=ov.vis.Viewport.Type.Left)

        # Initialize the pipeline
        self.pipeline = None

        # Create the OVITO widget
        self.ovito_widget = ov.gui.create_qwidget(self.viewport, self)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self.ovito_widget)

    def set_pipeline(self, gsd_file: str):
        """Set the pipeline from a GSD file path."""
        # Validate path
        if not gsd_file or not gsd_file.strip():
            self.clear()
            return

        gsd_path = pathlib.Path(gsd_file)
        if not gsd_path.exists() or not gsd_path.is_file():
            self.clear()
            return

        self.gsd_file = str(gsd_path)

        # Clear existing pipelines
        self._clear_pipelines()

        # Import and display the GSD file
        self.pipeline = ov.io.import_file(self.gsd_file)
        self.pipeline.add_to_scene()
        if hasattr(self.viewport, "zoom_all"):
            self.viewport.zoom_all()

    def _clear_pipelines(self):
        """Clear all pipelines from the scene."""
        # Remove our own pipeline first
        if self.pipeline is not None:
            try:
                self.pipeline.remove_from_scene()
            except Exception:
                pass
            self.pipeline = None

        # Clear all pipelines from scene
        if hasattr(ov.scene, "pipelines"):
            try:
                for p in list(ov.scene.pipelines):
                    try:
                        p.remove_from_scene()
                    except Exception:
                        pass
            except Exception:
                pass

    def clear(self):
        """Clear all pipelines and reset state."""
        self._clear_pipelines()
        self.gsd_file = None

    def refresh(self):
        """Refresh the graph view widget."""
        if self.controller is None:
            self.clear()
            return

        handler = self.controller.get_selected_handler()
        if handler is None:
            self.clear()
            return

        pipeline = self.controller.get_selected_extracted_graph()
        if pipeline:
            self.set_pipeline(pipeline)
        else:
            self.clear()
