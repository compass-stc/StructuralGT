"""Analysis widget for StructuralGT GUI."""

import json
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QComboBox,
    QSlider,
    QCheckBox,
    QPushButton,
    QSizePolicy,
)
from service.main_controller import MainController
from view.dialogs.file_dialog import export_file


class AnalysisWidget(QWidget):
    """Analysis widget for StructuralGT GUI."""

    def __init__(self, controller: MainController, parent):
        """Initialize the analysis widget."""
        super().__init__(parent)
        self.controller = controller
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        self.binarizer_widget = BinarizerWidget(
            controller=controller, parent=self
        )
        layout.addWidget(self.binarizer_widget, alignment=Qt.AlignTop)
        layout.addSpacing(10)

        self.compute_graph_properties_widget = ComputeGraphPropertiesWidget(
            controller=controller, parent=self
        )
        layout.addWidget(
            self.compute_graph_properties_widget, alignment=Qt.AlignTop
        )
        layout.addStretch(1)


class BinarizerWidget(QWidget):
    """Binarizer widget for StructuralGT GUI."""

    def __init__(self, controller: MainController, parent):
        """Initialize the binarizer widget."""
        super().__init__(parent)
        self.controller = controller
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)

        checkbox_layout = QVBoxLayout()
        checkbox_layout.setContentsMargins(0, 0, 0, 0)
        checkbox_layout.setSpacing(5)

        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_layout.setSpacing(5)

        label = QLabel("Binarize Filter", self)
        label.setAlignment(Qt.AlignCenter)

        self.threshold_combo = QComboBox(self)
        self.threshold_combo.addItems(["Global", "Adaptive", "OTSU"])

        self.gamma_slider = LabeledSlider(
            "Gamma",
            initial=1.00,
            minimum=0.01,
            maximum=10,
            step=0.01,
            decimals=2,
            parent=self,
        )

        self.median_filter_checkbox = QCheckBox("Median Filter", self)
        self.median_autolevel_checkbox = QCheckBox("Auto Level", self)
        self.gaussian_blur_checkbox = QCheckBox("Gaussian Blur", self)
        self.foreground_dark_checkbox = QCheckBox("Foreground Dark", self)
        self.laplacian_checkbox = QCheckBox("Laplacian", self)
        self.scharr_checkbox = QCheckBox("Scharr", self)
        self.sobel_checkbox = QCheckBox("Sobel", self)
        self.lowpass_checkbox = QCheckBox("Lowpass", self)

        self.threshold_slider = LabeledSlider(
            "Threshold",
            initial=128,
            minimum=0,
            maximum=256,
            step=0.01,
            decimals=2,
            parent=self,
        )
        self.adaptive_kernel_slider = LabeledSlider(
            "Adaptive Kernel",
            initial=1,
            minimum=1,
            maximum=2000,
            step=1,
            decimals=0,
            parent=self,
        )
        self.blur_kernel_slider = LabeledSlider(
            "Blur Kernel",
            initial=0,
            minimum=0,
            maximum=400,
            step=1,
            decimals=0,
            parent=self,
        )
        self.window_size_slider = LabeledSlider(
            "Window Size",
            initial=0,
            minimum=0,
            maximum=10,
            step=1,
            decimals=0,
            parent=self,
        )

        self.reset_button = QPushButton("Reset", self)
        self.export_button = QPushButton("Export", self)
        self.reset_button.clicked.connect(self._on_reset_button_clicked)
        self.export_button.clicked.connect(self._on_export_button_clicked)

        button_layout.addWidget(self.reset_button)
        button_layout.addWidget(self.export_button)

        checkbox_layout.addWidget(self.median_filter_checkbox)
        checkbox_layout.addWidget(self.median_autolevel_checkbox)
        checkbox_layout.addWidget(self.gaussian_blur_checkbox)
        checkbox_layout.addWidget(self.foreground_dark_checkbox)
        checkbox_layout.addWidget(self.laplacian_checkbox)
        checkbox_layout.addWidget(self.scharr_checkbox)
        checkbox_layout.addWidget(self.sobel_checkbox)
        checkbox_layout.addWidget(self.lowpass_checkbox)

        layout.addWidget(label)
        layout.addWidget(self.threshold_combo)
        layout.addWidget(self.gamma_slider)
        layout.addLayout(checkbox_layout)
        layout.addWidget(self.threshold_slider)
        layout.addWidget(self.adaptive_kernel_slider)
        layout.addWidget(self.blur_kernel_slider)
        layout.addWidget(self.window_size_slider)
        layout.addLayout(button_layout)

        # Debounce timer
        self._binarize_timer = QTimer(self)
        self._binarize_timer.setSingleShot(True)
        self._binarize_timer.timeout.connect(self._on_binarize_timeout)

        self._connect_binarize_signals()

    def _on_reset_button_clicked(self):
        self.threshold_combo.setCurrentIndex(0)
        self.gamma_slider.setValue(1.00)
        self.threshold_slider.setValue(128)
        self.adaptive_kernel_slider.setValue(1)
        self.blur_kernel_slider.setValue(0)
        self.window_size_slider.setValue(0)
        self.median_filter_checkbox.setChecked(False)
        self.median_autolevel_checkbox.setChecked(False)
        self.gaussian_blur_checkbox.setChecked(False)
        self.foreground_dark_checkbox.setChecked(False)
        self.laplacian_checkbox.setChecked(False)
        self.scharr_checkbox.setChecked(False)
        self.sobel_checkbox.setChecked(False)
        self.lowpass_checkbox.setChecked(False)

    def _on_export_button_clicked(self):
        handler = self.controller.get_selected_handler()
        if handler:
            file_path = export_file(
                parent=self,
                default_filename="img_options.json",
                file_filter="JSON (*.json)",
                default_dir=str(handler["paths"]["input_dir"]),
            )
            if file_path:
                binarize_options = handler["binarize_options"]
                with open(file_path, "w") as f:
                    json.dump(binarize_options, f)

    def _connect_binarize_signals(self):
        self.threshold_combo.currentTextChanged.connect(self._trigger_binarize)
        self.gamma_slider.valueChanged.connect(self._trigger_binarize)
        self.threshold_slider.valueChanged.connect(self._trigger_binarize)
        self.adaptive_kernel_slider.valueChanged.connect(
            self._trigger_binarize
        )
        self.blur_kernel_slider.valueChanged.connect(self._trigger_binarize)
        self.window_size_slider.valueChanged.connect(self._trigger_binarize)
        self.median_filter_checkbox.toggled.connect(self._trigger_binarize)
        self.median_autolevel_checkbox.toggled.connect(self._trigger_binarize)
        self.gaussian_blur_checkbox.toggled.connect(self._trigger_binarize)
        self.foreground_dark_checkbox.toggled.connect(self._trigger_binarize)
        self.laplacian_checkbox.toggled.connect(self._trigger_binarize)
        self.scharr_checkbox.toggled.connect(self._trigger_binarize)
        self.sobel_checkbox.toggled.connect(self._trigger_binarize)
        self.lowpass_checkbox.toggled.connect(self._trigger_binarize)

    def _trigger_binarize(self):
        self._binarize_timer.stop()
        self._binarize_timer.start(500)

    def _on_binarize_timeout(self):
        if self.controller:
            options = self._get_binarize_options()
            self.controller.binarize_selected_network(options)

    def _get_binarize_options(self):
        return {
            "Thresh_method": self.threshold_combo.currentIndex(),
            "gamma": float(self.gamma_slider.value()),
            "md_filter": 1 if self.median_filter_checkbox.isChecked() else 0,
            "g_blur": 1 if self.gaussian_blur_checkbox.isChecked() else 0,
            "autolvl": 1 if self.median_autolevel_checkbox.isChecked() else 0,
            "fg_color": 1 if self.foreground_dark_checkbox.isChecked() else 0,
            "laplacian": 1 if self.laplacian_checkbox.isChecked() else 0,
            "scharr": 1 if self.scharr_checkbox.isChecked() else 0,
            "sobel": 1 if self.sobel_checkbox.isChecked() else 0,
            "lowpass": 1 if self.lowpass_checkbox.isChecked() else 0,
            "asize": int(self.adaptive_kernel_slider.value()) * 2 + 1,
            "bsize": int(self.blur_kernel_slider.value()) * 2 + 1,
            "wsize": int(self.window_size_slider.value()) * 2 + 1,
            "thresh": float(self.threshold_slider.value()),
        }


class ComputeGraphPropertiesWidget(QWidget):
    """Graph Properties widget for StructuralGT GUI."""

    def __init__(self, controller: MainController, parent):
        """Initialize the graph properties widget."""
        super().__init__(parent)
        self.controller = controller
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)

        checkbox_layout = QVBoxLayout()
        checkbox_layout.setContentsMargins(0, 0, 0, 0)
        checkbox_layout.setSpacing(5)

        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(0, 0, 0, 0)
        button_layout.setSpacing(5)

        label = QLabel("Graph Properties", self)
        label.setAlignment(Qt.AlignCenter)

        self.diameter_checkbox = QCheckBox("Diameter", self)
        self.density_checkbox = QCheckBox("Density", self)
        self.average_clustering_checkbox = QCheckBox(
            "Average Clustering Coefficient", self
        )
        self.assortativity_checkbox = QCheckBox("Assortativity", self)
        self.average_closeness_checkbox = QCheckBox(
            "Average Closeness Centrality", self
        )
        self.average_degree_checkbox = QCheckBox("Average Degree", self)
        self.nematic_order_checkbox = QCheckBox(
            "Nematic Order Parameter", self
        )
        self.effective_resistance_checkbox = QCheckBox(
            "Effective Resistance", self
        )

        self.extract_button = QPushButton("Extract Graph", self)
        self.compute_button = QPushButton("Compute", self)

        checkbox_layout.addWidget(self.diameter_checkbox)
        checkbox_layout.addWidget(self.density_checkbox)
        checkbox_layout.addWidget(self.average_clustering_checkbox)
        checkbox_layout.addWidget(self.assortativity_checkbox)
        checkbox_layout.addWidget(self.average_closeness_checkbox)
        checkbox_layout.addWidget(self.average_degree_checkbox)
        checkbox_layout.addWidget(self.nematic_order_checkbox)
        checkbox_layout.addWidget(self.effective_resistance_checkbox)

        button_layout.addWidget(self.extract_button)
        button_layout.addWidget(self.compute_button)

        layout.addWidget(label)
        layout.addLayout(checkbox_layout)
        layout.addLayout(button_layout)

        self.extract_button.clicked.connect(self._on_extract_graph)
        self.compute_button.clicked.connect(self._on_compute_graph_properties)

    def _on_extract_graph(self):
        self.controller.extract_graph_from_selected_network()

    def _on_compute_graph_properties(self):
        options = self._get_graph_properties_options()
        self.controller.compute_graph_properties_from_selected_network(options)

    def _get_graph_properties_options(self):
        return {
            "diameter": self.diameter_checkbox.isChecked(),
            "density": self.density_checkbox.isChecked(),
            "average_clustering_coefficient": (
                self.average_clustering_checkbox.isChecked(),
            ),
            "assortativity": self.assortativity_checkbox.isChecked(),
            "average_closeness": self.average_closeness_checkbox.isChecked(),
            "average_degree": self.average_degree_checkbox.isChecked(),
            "nematic_order_parameter": self.nematic_order_checkbox.isChecked(),
            "effective_resistance": (
                self.effective_resistance_checkbox.isChecked(),
            ),
        }


class LabeledSlider(QWidget):
    """Slider with label and value readout."""

    valueChanged = Signal(float)

    def __init__(
        self,
        text,
        initial,
        minimum=0.0,
        maximum=1.0,
        step=0.1,
        decimals=1,
        parent=None,
    ):
        """Initialize the labeled slider."""
        super().__init__(parent)
        self._decimals = max(0, decimals)
        self._multiplier = 10**self._decimals

        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 0, 5, 0)
        layout.setSpacing(5)

        self.label = QLabel(text, self)
        self.slider = QSlider(Qt.Horizontal, self)
        self.slider.setRange(
            int(minimum * self._multiplier), int(maximum * self._multiplier)
        )
        self.slider.setSingleStep(max(1, int(step * self._multiplier)))

        self.value_label = QLabel("", self)

        layout.addWidget(self.label)
        layout.addWidget(self.slider)
        layout.addWidget(self.value_label)

        self.slider.setValue(int(initial * self._multiplier))
        self.value_label.setText(self._format_value(self.slider.value()))
        self.slider.valueChanged.connect(self._on_value_changed)

    def _format_value(self, raw_value):
        return f"{raw_value / self._multiplier:.{self._decimals}f}"

    def _on_value_changed(self, raw_value):
        self.value_label.setText(self._format_value(raw_value))
        self.valueChanged.emit(raw_value / self._multiplier)

    def setValue(self, value):
        """Set the value of the labeled slider."""
        self.slider.setValue(int(value * self._multiplier))

    def value(self):
        """Get the value of the labeled slider."""
        return self.slider.value() / self._multiplier
