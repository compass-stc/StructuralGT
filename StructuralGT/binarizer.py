# Copyright (c) 2023-2024 The Regents of the University of Michigan.
# This file is from the StructuralGT project, released under the BSD 3-Clause
# License.

import json
import os

import cv2 as cv
import matplotlib.pyplot as plt
from IPython.display import display
from ipywidgets import Layout, interactive, widgets

from StructuralGT import process_image


class Binarizer:
    """Class for providing realtime image binarization to determine optimal
    image processing parameters.

    Args:
        filename (str):
            The name of the file to binarize.
    """

    def binarize_widget(
        self,
        Thresh_method,
        gamma,
        md_filter,
        autolvl,
        g_blur,
        fg_color,
        laplacian,
        scharr,
        sobel,
        lowpass,
        thr,
        asize,
        bsize,
        wsize,
        export,
    ):
        """The widget method. Interacted with by calling :meth:`binarize()`."""

        gray_image = cv.imread(self.filename, cv.IMREAD_GRAYSCALE)
        Thresh_dict = {"Global": 0, "Adaptive": 1, "OTSU": 2}
        options = dict(
            Thresh_method=Thresh_dict[Thresh_method],
            gamma=gamma,
            md_filter=int(md_filter),
            g_blur=int(g_blur),
            autolvl=int(autolvl),
            fg_color=int(fg_color),
            laplacian=int(laplacian),
            scharr=int(scharr),
            sobel=int(sobel),
            lowpass=int(lowpass),
            asize=int(asize) * 2 + 1,
            bsize=int(bsize) * 2 + 1,
            wsize=int(wsize) * 2 + 1,
            thresh=thr,
        )

        if export:
            if self.export_dir is None:
                self.export_dir = os.path.split(self.filename)[0]
            with open(self.export_dir + "/img_options.json", "w") as fp:
                json.dump(options, fp)

        _, binary_image, _ = process_image.binarize(gray_image, options)
        _, self.ax = plt.subplots()
        self.ax.imshow(binary_image, cmap="gray")
        plt.show()

    def __init__(self, filename, export_dir=None):
        """Method for generating the interactive binarization widget.

        Args:
            export (str, optional):
                The directory to export the :code:`img_options.json` file. If
                no arguement given, exports to parent directory of image.
        """

        self.filename = filename
        self.export_dir = export_dir

        item_layout = Layout(
            display="flex", flex_flow="row", justify_content="space-between"
        )

        Thresh_method = widgets.Dropdown(
            options=["Global", "Adaptive", "OTSU"],
            description="Threshold",
            layout=item_layout,
        )
        gamma = widgets.FloatSlider(
            description="Gamma", value=1, min=0.001, max=10, layout=item_layout
        )
        md_filter = widgets.Checkbox(
            description="Median filter", value=0, layout=item_layout
        )
        autolvl = widgets.Checkbox(description="Autolevel", value=0,
                                   layout=item_layout)
        g_blur = widgets.Checkbox(
            description="Gaussian Blur", value=0, layout=item_layout
        )
        fg_color = widgets.Checkbox(
            description="Foreground dark", value=0, layout=item_layout
        )
        laplacian = widgets.Checkbox(
            description="Laplacian", value=0, layout=item_layout
        )
        scharr = widgets.Checkbox(description="Scharr", value=0,
                                  layout=item_layout)
        sobel = widgets.Checkbox(description="Sobel", value=0,
                                 layout=item_layout)
        lowpass = widgets.Checkbox(description="Lowpass", value=0,
                                   layout=item_layout)
        thr = widgets.FloatSlider(
            description="Threshold",
            value=128,
            min=0,
            max=256,
            layout=item_layout,
        )
        asize = widgets.FloatSlider(
            description="Adaptive threshold kernel",
            value=1,
            min=1,
            max=2000,
            layout=item_layout,
        )
        bsize = widgets.FloatSlider(
            description="Blurring kernel size",
            value=0,
            min=0,
            max=400,
            layout=item_layout,
        )
        wsize = widgets.FloatSlider(
            description="Window size",
            value=0,
            min=0,
            max=10,
            layout=item_layout,
        )
        export = widgets.Checkbox(description="Export", value=0,
                                  layout=item_layout)

        self.w = interactive(
            self.binarize_widget,
            Thresh_method=Thresh_method,
            gamma=gamma,
            md_filter=md_filter,
            autolvl=autolvl,
            g_blur=g_blur,
            fg_color=fg_color,
            laplacian=laplacian,
            scharr=scharr,
            sobel=sobel,
            lowpass=lowpass,
            thr=thr,
            asize=asize,
            bsize=bsize,
            wsize=wsize,
            export=export,
            filename=self.filename,
        )

        self.w.layout = Layout(
            display="flex",
            flex_flow="row wrap",
            border="solid 2px",
            align_items="stretch",
            width="38%",
        )

        display(self.w)
