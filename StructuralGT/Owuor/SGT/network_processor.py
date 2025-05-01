# SPDX-License-Identifier: GNU GPL v3

"""
Processes 2D or 3D images and generate a fiber graph network.
"""

import re
import os
import sys
import cv2
import pydicom
import logging
import numpy as np
import nibabel as nib
import matplotlib.pyplot as plt
from PIL import Image
from dataclasses import dataclass
from collections import defaultdict

from .fiber_network import FiberNetworkBuilder
from .progress_update import ProgressUpdate
from .base_image import BaseImage

logger = logging.getLogger("SGT App")
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s", stream=sys.stdout)

Image.MAX_IMAGE_PIXELS = None  # Disable limit on maximum image size
ALLOWED_IMG_EXTENSIONS = ('*.jpg', '*.png', '*.jpeg', '*.tif', '*.tiff', '*.qptiff')


class NetworkProcessor(ProgressUpdate):
    """
    A class for processing and preparing 2D or 3D microscopy images for building a fiber graph network.

    Args:
        img_path (str): input image path
        out_dir (str): directory path for storing results.
    """

    @dataclass
    class ImageBatch:
        numpy_image: np.ndarray
        images: list[BaseImage]
        is_2d: bool
        shape: tuple
        props: list
        scale_factor: float
        scaling_options: list
        selected_images: set
        current_view: str
        graph_obj: FiberNetworkBuilder

    def __init__(self, img_path, out_dir, auto_scale=True):
        """
        A class for processing and preparing microscopy images for building a fiber graph network.

        Args:
            img_path (str | list): input image path
            out_dir (str): directory path for storing results.

        >>>
        >>> i_path = "path/to/image"
        >>> o_dir = ""
        >>>
        >>> imp_obj = NetworkProcessor(i_path, o_dir)
        >>> imp_obj.apply_img_filters()
        """
        super(NetworkProcessor, self).__init__()
        self.img_path: str = img_path if type(img_path) is str else img_path[0]
        self.output_dir: str = out_dir
        self.auto_scale: bool = auto_scale
        self.image_batches: list[NetworkProcessor.ImageBatch] = []
        self.selected_batch: int = 0
        self._initialize_image_batches(self._load_img_from_file(img_path))

    def _load_img_from_file(self, file: list | str):
        """
        Read the image and save it as an OpenCV object.

        Most 3D images are like layers of multiple image frames layered on-top of each other. The image frames may be
        images of the same object/item through time or through space (i.e., from different angles). Our approach is to
        separate these frames, extract GT graphs from them, and then the layer back from the extracted graphs in the same order.

        Our software will display all the frames retrieved from the 3D image (automatically downsample large ones
        depending on the user-selected re-scaling options), and allows the user to select which frames to run
        GT computations on. (Some frames are just too noisy to be used.)

        Again, our software provides a button that allows the user to select which frames are used to reconstruct the
        layered GT graphs in the same order as their respective frames.

        :param file: The file path.
        :return: list[NetworkProcessor.ImageBatch]
        """

        # First file if it's a list
        ext = os.path.splitext(file[0])[1].lower() if (type(file) is list) else os.path.splitext(file)[1].lower()
        try:
            if ext in ['.png', '.jpg', '.jpeg']:
                image_groups = defaultdict(list)
                if type(file) is list:
                    for img in file:
                        # Create clusters/groups of similar size images
                        frame = cv2.imread(img, cv2.IMREAD_UNCHANGED)
                        h, w = frame.shape[:2]
                        image_groups[(h, w)].append(frame)
                else:
                    # Load standard 2D images with OpenCV
                    image = cv2.imread(file, cv2.IMREAD_UNCHANGED)
                    if image is None:
                        raise ValueError(f"Failed to load {file}")
                    # Cluster the images into batches based on (h, w) size
                    h, w = image.shape[:2]
                    image_groups[(h, w)].append(image)
                img_batch_groups = NetworkProcessor.create_img_batch_groups(image_groups, self.auto_scale)
                return img_batch_groups
            elif ext in ['.tif', '.tiff', '.qptiff']:
                image_groups = defaultdict(list)
                if type(file) is list:
                    for img in file:
                        # Create clusters/groups of similar size images
                        frame = cv2.imread(img, cv2.IMREAD_UNCHANGED)
                        h, w = frame.shape[:2]
                        image_groups[(h, w)].append(frame)
                else:
                    # Try load multi-page TIFF using PIL
                    img = Image.open(file)
                    while True:
                        # Create clusters/groups of similar size images
                        frame = np.array(img)  # Convert the current frame to the numpy array
                        # Cluster the images into batches based on (h, w) size
                        h, w = frame.shape[:2]
                        image_groups[(h, w)].append(frame)
                        try:
                            # Move to the next frame
                            img.seek(img.tell() + 1)
                        except EOFError:
                            # Stop when all frames are read
                            break
                img_batch_groups = NetworkProcessor.create_img_batch_groups(image_groups, self.auto_scale)
                return img_batch_groups
            elif ext in ['.nii', '.nii.gz']:
                # Load NIfTI image using nibabel
                img_nib = nib.load(file)
                data = img_nib.get_fdata()
                # Normalize and convert to uint8 for OpenCV compatibility
                data = cv2.normalize(data, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
                return data
            elif ext == '.dcm':
                # Load DICOM image using pydicom
                dcm = pydicom.dcmread(file)
                data = dcm.pixel_array
                # Normalize and convert to uint8 if needed
                data = cv2.normalize(data, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
                return data
            else:
                raise ValueError(f"Unsupported file format: {ext}")
        except Exception as err:
            logging.exception(f"Error loading {file}:", err, extra={'user': 'SGT Logs'})
            return None

    def _initialize_image_batches(self, img_batches: list[ImageBatch]):
        """
        Retrieve all image slices of the selected image batch. If the image is 2D, only one slice exists
        if it is 3D, then multiple slices exist.
        """

        # Check if image batches exist
        if len(img_batches) == 0:
            raise ValueError("No images available! Please add at least one image.")
        
        for i, img_batch in enumerate(img_batches):
            img_data = img_batch.numpy_image
            scale_factor = img_batch.scale_factor

            # Load images for processing
            if img_data is None:
                raise ValueError(f"Problem with images in batch {i}!")

            has_alpha, _ = BaseImage.check_alpha_channel(img_data)
            image_list = []
            if (len(img_data.shape) >= 3) and (not has_alpha):
                # If the image has shape (d, h, w) and does not an alpha channel which is less than 4 - (h, w, a)
                image_list = [BaseImage(img, scale_factor) for img in img_data]
            else:
                img_obj = BaseImage(img_data, scale_factor)
                image_list.append(img_obj)

            is_2d = True
            if len(image_list) == 1:
                if len(img_data.shape) == 3 and image_list[0].has_alpha_channel:
                    logging.info("Image is 2D with Alpha Channel.", extra={'user': 'SGT Logs'})
                else:
                    logging.info("Image is 2D.", extra={'user': 'SGT Logs'})
            elif len(image_list) > 1:
                is_2d = False
                logging.info("Image is 3D.", extra={'user': 'SGT Logs'})


            img_batch.images = image_list
            img_batch.is_2d = is_2d
            self.update_image_props(img_batch)
        self.image_batches = img_batches

    def select_image_batch(self, sel_batch_idx: int, selected_images: set = None):
        """
        Update the selected image batch and the selected image slices.

        Args:
            sel_batch_idx: index of the selected image batch
            selected_images: indices of the selected image slices.

        Returns:

        """

        if sel_batch_idx >= len(self.image_batches):
            raise ValueError(f"Selected image batch {sel_batch_idx} out of range! Select in range 0-{len(self.image_batches)}")

        self.selected_batch = sel_batch_idx
        self.update_image_props(self.image_batches[sel_batch_idx])
        self.reset_img_filters()

        if selected_images is None:
            return

        if type(selected_images) is set:
            self.image_batches[sel_batch_idx].selected_images = selected_images

    def track_progress(self, value, msg):
        self.update_status([value, msg])

    def apply_img_filters(self, filter_type=2):
        """
        Executes function for processing image filters and converting the resulting image into a binary.

        Filter Types:
        1 - Just Image Filters
        2 - Both Image and Binary (1 and 2) Filters

        :return: None
        """

        self.update_status([10, "Processing image..."])
        if filter_type == 2:
            self.reset_img_filters()
        
        sel_batch = self.get_selected_batch()
        progress = 10
        incr = 90 / len(sel_batch.images) - 1
        for i in range(len(sel_batch.images)):
            img_obj = sel_batch.images[i]
            if i not in sel_batch.selected_images:
                img_obj.img_mod, img_obj.img_bin = None, None
                continue

            if progress < 100:
                progress += incr
                self.update_status([progress, "Image processing in progress..."])

            img_data = img_obj.img_2d.copy()
            img_obj.img_mod = img_obj.process_img(image=img_data)

            if filter_type == 2:
                img_mod = img_obj.img_mod.copy()
                img_obj.img_bin = img_obj.binarize_img(img_mod)
            img_obj.get_pixel_width()

        self.update_status([100, "Image processing complete..."])

    def reset_img_filters(self):
        """Delete existing filters that have been applied on the image."""
        sel_batch = self.get_selected_batch()
        for img_obj in sel_batch.images:
            img_obj.img_mod, img_obj.img_bin = None, None
            sel_batch.graph_obj.reset_graph()

    def apply_img_scaling(self):
        """Re-scale (downsample or up-sample) a 2D image or 3D images to a specified size"""

        # scale_factor = 1
        sel_batch = self.get_selected_batch()
        if len(sel_batch.images) <= 0:
            return

        scale_size = 0
        for scale_item in sel_batch.scaling_options:
            try:
                scale_size = scale_item["dataValue"] if scale_item["value"] == 1 else scale_size
            except KeyError:
                continue

        if scale_size <= 0:
            return

        img_px_size = 1
        for img_obj in sel_batch.images:
            img = img_obj.img_raw
            temp_px = max(img.shape[0], img.shape[1])
            img_px_size = temp_px if temp_px > img_px_size else img_px_size
        scale_factor = scale_size / img_px_size

        # Resize (Downsample) all frames to the smaller pixel size while maintaining the aspect ratio
        for img_obj in sel_batch.images:
            img = img_obj.img_raw.copy()
            scale_size = scale_factor * max(img.shape[0], img.shape[1])
            img_small, _ = BaseImage.resize_img(scale_size, img)
            if img_small is None:
                # raise Exception("Unable to Rescale Image")
                return
            img_obj.img_2d = img_small
            img_obj.scale_factor = scale_factor
        self.update_image_props(sel_batch)

    def crop_image(self, x: int, y: int, crop_w: int, crop_h: int, actual_w: int, actual_h: int):
        """
        A function that crops images into a new box dimension.

        :param x: Left coordinate of cropping box.
        :param y: Top coordinate of cropping box.
        :param crop_w: Width of cropping box.
        :param crop_h: Height of cropping box.
        :param actual_w: Width of actual image.
        :param actual_h: Height of actual image.
        """
        sel_batch = self.get_selected_batch()
        if len(sel_batch.selected_images) > 0:
            [sel_batch.images[i].apply_img_crop(x, y, crop_w, crop_h, actual_w, actual_h) for i in sel_batch.selected_images]
        self.update_image_props(sel_batch)
        sel_batch.current_view = 'processed'

    def undo_cropping(self):
        """
        A function that restores the image to its original size.
        """
        sel_batch = self.get_selected_batch()
        if len(sel_batch.selected_images) > 0:
            [sel_batch.images[i].init_image() for i in sel_batch.selected_images]
        self.update_image_props(sel_batch)

    def build_graph_network(self):
        """Generates or extracts graphs of selected images."""

        self.update_status([0, "Starting graph extraction..."])
        try:
            # Get the selected batch
            sel_batch = self.get_selected_batch()
            sel_batch.current_view = 'graph'

            # Get binary image
            sel_images = self.get_selected_images(sel_batch)
            img_bin = [img.img_bin for img in sel_images]
            img_3d = [img.img_2d for img in sel_images]
            img_bin = np.asarray(img_bin)
            img_3d = np.asarray(img_3d)

            # Get the selected batch's graph object and generate the graph
            px_size = float(sel_batch.images[0].configs["pixel_width"]["value"])  # First BaseImage in batch
            rho_val = float(sel_batch.images[0].configs["resistivity"]["value"])  # First BaseImage in batch
            f_name, out_dir = self.get_filenames()

            sel_batch.graph_obj.abort = False
            sel_batch.graph_obj.add_listener(self.track_progress)
            sel_batch.graph_obj.fit_graph(out_dir, img_bin, img_3d, sel_batch.is_2d, px_size, rho_val, image_file=f_name)
            sel_batch.graph_obj.remove_listener(self.track_progress)
            self.abort = sel_batch.graph_obj.abort
            if self.abort:
                sel_batch.current_view = 'processed'
                return
        except Exception as err:
            self.abort = True
            logging.info(f"Error creating graph from image binary.")
            logging.exception("Graph Extraction Error: %s", err, extra={'user': 'SGT Logs'})
            return

    def get_filenames(self, image_path: str = None):
        """
        Splits the image path into file name and image directory.

        :param image_path: Image directory path.

        Returns:
            filename (str): image file name., output_dir (str): image directory path.
        """

        img_dir, filename = os.path.split(self.img_path) if image_path is None else os.path.split(image_path)
        output_dir = img_dir if self.output_dir == '' else self.output_dir

        for ext in ALLOWED_IMG_EXTENSIONS:
            ext = ext.replace('*', '')
            pattern = re.escape(ext) + r'$'
            filename = re.sub(pattern, '', filename)
        return filename, output_dir

    def get_selected_batch(self):
        """
        Retrieved data of the current selected batch.
        """
        return self.image_batches[self.selected_batch]

    def get_selected_images(self, selected_batch: ImageBatch):
        """
        Get indices of selected images.
        :param selected_batch: The selected batch ImageBatch object.
        """
        if selected_batch is None:
           selected_batch = self.get_selected_batch()

        sel_images = [selected_batch.images[i] for i in selected_batch.selected_images]
        return sel_images

    def update_image_props(self, selected_batch: ImageBatch = None):
        """
        A method that retrieves image properties and stores them in a list-array.

        :param selected_batch: ImageBatch data object.

        Returns: list of image properties

        """

        if selected_batch is None:
            return

        f_name, _ = self.get_filenames()
        if len(selected_batch.images) > 1:
            # (Depth, Height, Width, Channels)
            alpha_channel = selected_batch.images[0].has_alpha_channel  # first image
            fmt = "Multi + Alpha" if alpha_channel else "Multi"
            num_dim = 3
        else:
            _, fmt = BaseImage.check_alpha_channel(selected_batch.images[0].img_raw)  # first image
            num_dim = 2

        slices = 0
        height, width = selected_batch.images[0].img_2d.shape[:2]  # first image
        if num_dim >= 3:
            slices = len(selected_batch.images)

        props = [
            ["Name", f_name],
            ["Height x Width", f"({width} x {height}) pixels"] if slices == 0 else ["Depth x H x W",
                                                                                    f"({slices} x {width} x {height}) pixels"],
            ["Dimensions", f"{num_dim}D"],
            ["Format", f"{fmt}"],
            # ["Pixel Size", "2nm x 2nm"]
        ]
        selected_batch.props = props

    def plot_images(self):
        """
        Create plot figures of original, processed, and binary image.

        :return:
        """

        figs = []
        sel_batch = self.get_selected_batch()
        sel_images = self.get_selected_images(sel_batch)
        is_3d = True if len(sel_images) > 1 else False

        for i, img in enumerate(sel_images):
            opt_img = img.configs
            raw_img = img.img_2d
            filtered_img = img.img_mod
            img_bin = img.img_bin

            img_histogram = cv2.calcHist([filtered_img], [0], None, [256], [0, 256])

            fig = plt.Figure(figsize=(8.5, 8.5), dpi=400)
            ax_1 = fig.add_subplot(2, 2, 1)
            ax_2 = fig.add_subplot(2, 2, 2)
            ax_3 = fig.add_subplot(2, 2, 3)
            ax_4 = fig.add_subplot(2, 2, 4)

            ax_1.set_title(f"Frame {i}: Original Image") if is_3d else ax_1.set_title(f"Original Image")
            ax_1.set_axis_off()
            ax_1.imshow(raw_img, cmap='gray')

            ax_2.set_title(f"Frame {i}: Processed Image") if is_3d else ax_2.set_title(f"Processed Image")
            ax_2.set_axis_off()
            ax_2.imshow(filtered_img, cmap='gray')

            ax_3.set_title(f"Frame {i}: Binary Image") if is_3d else ax_3.set_title(f"Binary Image")
            ax_3.set_axis_off()
            ax_3.imshow(img_bin, cmap='gray')

            ax_4.set_title(f"Frame {i}: Histogram of Processed Image") if is_3d else ax_4.set_title(f"Histogram of Processed Image")
            ax_4.set(yticks=[], xlabel='Pixel values', ylabel='Counts')
            ax_4.plot(img_histogram)
            if opt_img["threshold_type"]["value"] == 0:
                thresh_arr = np.array(
                    [[int(opt_img["global_threshold_value"]["value"]), int(opt_img["global_threshold_value"]["value"])],
                     [0, max(img_histogram)]], dtype='object')
                ax_4.plot(thresh_arr[0], thresh_arr[1], ls='--', color='black')
            elif opt_img["threshold_type"]["value"] == 2:
                otsu_val = opt_img["otsu"]["value"]
                thresh_arr = np.array([[otsu_val, otsu_val],
                                       [0, max(img_histogram)]], dtype='object')
                ax_4.plot(thresh_arr[0], thresh_arr[1], ls='--', color='black')
            figs.append(fig)
        return figs

    def save_images_to_file(self):
        """
        Write images to a file.
        """

        sel_batch = self.get_selected_batch()
        sel_images = self.get_selected_images(sel_batch)
        is_3d = True if len(sel_images) > 1 else False
        img_file_name, out_dir = self.get_filenames()

        for i, img in enumerate(sel_images):
            if img.configs["save_images"]["value"] == 0:
                continue

            filename = f"{img_file_name}_Frame{i}" if is_3d else ''
            pr_filename = filename + "_processed.jpg"
            bin_filename = filename + "_binary.jpg"
            img_file = os.path.join(out_dir, pr_filename)
            bin_file = os.path.join(out_dir, bin_filename)

            if img.img_mod is not None:
                cv2.imwrite(str(img_file), img.img_mod)

            if img.img_bin is not None:
                cv2.imwrite(str(bin_file), img.img_bin)

        """sel_batch = self.get_selected_batch()
        gsd_filename = img_file_name + "_skel.gsd"
        gsd_file = os.path.join(out_dir, gsd_filename)
        if sel_batch.graph_obj.skel_obj.skeleton is not None:
            write_gsd_file(gsd_file, sel_batch.graph_obj.skel_obj.skeleton)"""

    @staticmethod
    def get_scaling_options(orig_size: float, auto_scale: bool):
        """"""
        orig_size = int(orig_size)
        if orig_size > 2048:
            recommended_size = 1024
            scaling_options = [1024, 2048, int(orig_size * 0.25), int(orig_size * 0.5), int(orig_size * 0.75),
                               orig_size]
        elif orig_size > 1024:
            recommended_size = 1024
            scaling_options = [1024, int(orig_size * 0.25), int(orig_size * 0.5), int(orig_size * 0.75), orig_size]
        else:
            recommended_size = orig_size
            scaling_options = [int(orig_size * 0.25), int(orig_size * 0.5), int(orig_size * 0.75), orig_size]

        # Remove duplicates and arrange in ascending order
        scaling_options = sorted(list(set(scaling_options)))
        scaling_data = []
        for val in scaling_options:
            data = {"text": f"{val} px", "value": 0, "dataValue": val}
            if val == orig_size:
                data["text"] = f"{data['text']}*"

            if val == recommended_size:
                data["text"] = f"{data['text']} (recommended)"
                data["value"] = 1 if auto_scale else 0
            scaling_data.append(data)
        return scaling_data

    @staticmethod
    def rescale_img(image_data, scale_options):
        """Downsample or up-sample image to a specified pixel size."""

        scale_factor = 1
        img_2d, img_3d = None, None

        if image_data is None:
            return None, scale_factor

        scale_size = 0
        for scale_item in scale_options:
            try:
                scale_size = scale_item["dataValue"] if scale_item["value"] == 1 else scale_size
            except KeyError:
                continue

        if scale_size <= 0:
            return None, scale_factor

        # if type(image_data) is np.ndarray:
        has_alpha, _ = BaseImage.check_alpha_channel(image_data)
        if (len(image_data.shape) == 2) or has_alpha:
            # If the image has shape (h, w) or shape (h, w, a), where 'a' - alpha channel which is less than 4
            img_2d, scale_factor = BaseImage.resize_img(scale_size, image_data)
            return img_2d, scale_factor

        # if type(image_data) is list:
        if (len(image_data.shape) >= 3) and (not has_alpha):
            # If the image has shape (d, h, w) and third is not alpha channel
            images = image_data
            img_3d = []
            for img in images:
                img_small, scale_factor = BaseImage.resize_img(scale_size, img)
                img_3d.append(img_small)
        return np.array(img_3d), scale_factor

    @staticmethod
    def create_img_batch_groups(img_groups: defaultdict, auto_scale: bool):
        """"""
        img_info_list = []
        for (h, w), images in img_groups.items():
            images_small = []
            scale_factor = 1
            scaling_opts = []
            images = np.array(images)
            max_size = max(h, w)
            if max_size > 0 and auto_scale:
                scaling_opts = NetworkProcessor.get_scaling_options(max_size, auto_scale)
                images_small, scale_factor = NetworkProcessor.rescale_img(images, scaling_opts)

            # Convert back to numpy arrays
            images = images_small if len(images_small) > 0 else images
            img_batch = NetworkProcessor.ImageBatch(
                numpy_image=images,
                images=[],
                is_2d=True,
                shape=(h, w),
                props=[],
                scale_factor=scale_factor,
                scaling_options=scaling_opts,
                selected_images=set(range(len(images))),
                current_view = 'original',              # 'original', 'binary', 'processed', 'graph'
                graph_obj=FiberNetworkBuilder()
            )
            img_info_list.append(img_batch)
        return img_info_list