# SPDX-License-Identifier: GNU GPL v3

"""
Pyside6 implementation of StructuralGT user interface.
"""

import os
import sys
from PySide6.QtCore import QObject
from PySide6.QtWidgets import QApplication
from PySide6.QtQml import QQmlApplicationEngine

from .gui_mcw.controller import MainController
from .gui_mcw.image_provider import ImageProvider


class MainWindow(QObject):
    def __init__(self):
        super().__init__()
        self.app = QApplication(sys.argv)
        self.ui_engine = QQmlApplicationEngine()

        # Register Controller for Dynamic Updates
        controller = MainController(qml_app=self.app)
        # Register Image Provider
        self.image_provider = ImageProvider(controller)

        # Test Image
        # img_path = "../../../../../datasets/InVitroBioFilm.png"
        # controller.imageChangedSignal.emit(0, img_path)

        # Set Models in QML Context
        self.ui_engine.rootContext().setContextProperty("imgThumbnailModel", controller.imgThumbnailModel)
        self.ui_engine.rootContext().setContextProperty("imagePropsModel", controller.imagePropsModel)
        self.ui_engine.rootContext().setContextProperty("graphPropsModel", controller.graphPropsModel)
        self.ui_engine.rootContext().setContextProperty("graphComputeModel", controller.graphComputeModel)
        self.ui_engine.rootContext().setContextProperty("microscopyPropsModel", controller.microscopyPropsModel)

        self.ui_engine.rootContext().setContextProperty("gteTreeModel", controller.gteTreeModel)
        self.ui_engine.rootContext().setContextProperty("gtcListModel", controller.gtcListModel)
        self.ui_engine.rootContext().setContextProperty("exportGraphModel", controller.exportGraphModel)
        self.ui_engine.rootContext().setContextProperty("imgBatchModel", controller.imgBatchModel)
        self.ui_engine.rootContext().setContextProperty("imgControlModel", controller.imgControlModel)
        self.ui_engine.rootContext().setContextProperty("imgBinFilterModel", controller.imgBinFilterModel)
        self.ui_engine.rootContext().setContextProperty("imgFilterModel", controller.imgFilterModel)
        self.ui_engine.rootContext().setContextProperty("imgScaleOptionModel", controller.imgScaleOptionModel)
        self.ui_engine.rootContext().setContextProperty("saveImgModel", controller.saveImgModel)
        self.ui_engine.rootContext().setContextProperty("img3dGridModel", controller.img3dGridModel)
        self.ui_engine.rootContext().setContextProperty("mainController", controller)
        self.ui_engine.addImageProvider("imageProvider", self.image_provider)

        # Load UI
        # Get the directory of the current script
        qml_dir = os.path.dirname(os.path.abspath(__file__))
        qml_name = 'sgt_qml/MainWindow.qml'
        qml_path = os.path.join(qml_dir, qml_name)
        self.ui_engine.load(qml_path)
        if not self.ui_engine.rootObjects():
            sys.exit(-1)


def pyside_app():
    """
    Initialize and run the PySide GUI application.
    Returns:

    """
    main_window = MainWindow()
    sys.exit(main_window.app.exec())
