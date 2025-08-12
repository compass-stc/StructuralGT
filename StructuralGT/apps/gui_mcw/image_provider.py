from PIL import Image, ImageQt  # Import ImageQt for conversion
from PySide6.QtGui import QPixmap
from PySide6.QtQuick import QQuickImageProvider
import cv2
import numpy as np
from matplotlib.backends.backend_agg import FigureCanvasAgg
from .handler import NetworkHandler

class ImageProvider(QQuickImageProvider):

    def __init__(self, img_controller):
        super().__init__(QQuickImageProvider.ImageType.Pixmap)
        self.pixmap = QPixmap()
        self.img_controller = img_controller
        self.img_controller.changeImageSignal.connect(self.handle_change_image)

    def handle_change_image(self):
        print("ImageProvider: handle_change_image called")
        image = self.img_controller.get_selected_handler()
        if image and isinstance(image, NetworkHandler):
            img_cv = None # img_cv must be a numpy array

            if image.display_type == "original":
                img_cv = image.network.image
                if image.dim == 3:
                    img_cv = img_cv[image.selected_slice_index, :, :]
            elif image.display_type == "binary":
                if image.dim == 3:
                    binary_img_path = "/Binarized/slice" + str(image.selected_slice_index+1).zfill(4) + ".tiff"
                    img_cv = cv2.imread(image.path + binary_img_path)
                else:
                    binary_img_path = "/Binarized/slice0000.tiff"
                    img_cv = cv2.imread(image.path.name + binary_img_path)
            elif image.display_type == "graph":
                if image.dim == 3:
                    img_cv = None
                    self.img_controller.load_graph()
                else:
                    ax = image.network.graph_plot()
                    fig = ax.get_figure()
                    fig.subplots_adjust(left=0, right=1, top=1, bottom=0)

                    canvas = FigureCanvasAgg(fig)
                    canvas.draw()

                    width, height = canvas.get_width_height()

                    buf = canvas.buffer_rgba()
                    img_cv = np.asarray(buf, dtype=np.uint8).reshape((height, width, 4))

                    self.img_controller.load_graph()
                

            if img_cv is not None:
                # Create Pixmap image
                self.pixmap = ImageQt.toqpixmap(Image.fromarray(img_cv))

            # Acknowledge the image load and send the signal to update QML
            image.img_loaded = True
            self.img_controller.imageChangedSignal.emit()
        else:
            print("ImageProvider: No images available to display.")
            self.pixmap = QPixmap()
            self.img_controller.imageChangedSignal.emit()

    def requestPixmap(self, img_id, requested_size, size):
        return self.pixmap