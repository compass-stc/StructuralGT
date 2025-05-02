# Copyright (c) 2023-2024 The Regents of the University of Michigan.
# This file is from the StructuralGT project, released under the BSD 3-Clause
# License.

# This file is a modified copy of the process_image.py file from the
# original StructuralGT project, which can be found at
# https://github.com/drewvecchio/StructuralGT.

import cv2
import numpy as np
# from __main__ import *
from skimage.filters.rank import autolevel, median
from skimage.morphology import disk


def adjust_gamma(image, gamma):
    if gamma != 1.00:
        invgamma = 1.00 / gamma
        table = np.array(
            [((i / 255.0) ** invgamma) * 255 for i in np.arange(0, 256)]
        ).astype("uint8")
        return cv2.LUT(image, table)
    else:
        return image


def Hamming_window(image, windowsize):
    w, h = image.shape
    ham1x = np.hamming(w)[:, None]  # 1D hamming
    ham1y = np.hamming(h)[:, None]  # 1D hamming
    f = cv2.dft(image.astype(np.float32), flags=cv2.DFT_COMPLEX_OUTPUT)
    ham2d = np.sqrt(np.dot(ham1x, ham1y.T)) ** windowsize
    f_shifted = np.fft.fftshift(f)
    f_complex = f_shifted[:, :, 0] * 1j + f_shifted[:, :, 1]
    f_filtered = ham2d * f_complex
    f_filtered_shifted = np.fft.fftshift(f_filtered)
    inv_img = np.fft.ifft2(f_filtered_shifted)  # inverse F.T.
    filtered_img = np.abs(inv_img)
    filtered_img -= filtered_img.min()
    filtered_img = filtered_img * 255 / filtered_img.max()
    filtered_img = filtered_img.astype(np.uint8)
    return filtered_img


def thresh_it(image, Threshtype, fg_color, asize, thresh):
    # only needed for OTSU threshold
    ret = 0

    if Threshtype == 0:
        if fg_color == 1:
            img_bin = cv2.threshold(image, thresh, 255,
                                    cv2.THRESH_BINARY_INV)[1]
        else:
            img_bin = cv2.threshold(image, thresh, 255, cv2.THRESH_BINARY)[1]

    # adaptive threshold generation
    elif Threshtype == 1:
        if fg_color == 1:
            img_bin = cv2.adaptiveThreshold(
                image,
                255,
                cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                cv2.THRESH_BINARY_INV,
                asize,
                2,
            )
        else:
            img_bin = cv2.adaptiveThreshold(
                image,
                255,
                cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                cv2.THRESH_BINARY,
                asize,
                2,
            )

    # OTSU threshold generation
    elif Threshtype == 2:
        if fg_color == 1:
            img_bin = cv2.threshold(
                image, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU
            )[1]
            ret = cv2.threshold(image, 0, 255,
                                cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)[0]
        else:
            img_bin = cv2.threshold(image, 0, 255,
                                    cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
            ret = cv2.threshold(image, 0, 255,
                                cv2.THRESH_BINARY + cv2.THRESH_OTSU)[0]
    else:
        raise ValueError("Threshtype must be 0,1 or 2")

    return img_bin, ret


def binarize(source, options):
    Threshtype = int(options["Thresh_method"])
    gamma = options["gamma"]
    md_filter = options["md_filter"]
    g_blur = options["g_blur"]
    autolvl = options["autolvl"]
    fg_color = options["fg_color"]
    laplacian = options["laplacian"]
    scharr = options["scharr"]
    sobel = options["sobel"]
    lowpass = options["lowpass"]
    asize = int(options["asize"])
    bsize = int(options["bsize"])
    wsize = int(options["wsize"])
    thresh = options["thresh"]

    global img
    global img_bin

    img = source

    img = adjust_gamma(img, gamma)

    # applies a low-pass filter
    if lowpass == 1:
        img = Hamming_window(img, wsize)

    darray = np.zeros((5, 5)) + 1
    footprint = disk(bsize)

    # applying median filter
    if md_filter == 1:
        img = median(img, darray)

    # applying gaussian blur
    if g_blur == 1:
        img = cv2.GaussianBlur(img, (bsize, bsize), 0)

    # applying autolevel filter
    if autolvl == 1:
        img = autolevel(img, footprint=footprint)

    if scharr == 1:
        ddepth = cv2.CV_16S
        grad_x = cv2.Scharr(img, ddepth, 1, 0)
        grad_y = cv2.Scharr(img, ddepth, 0, 1)
        abs_grad_x = cv2.convertScaleAbs(grad_x)
        abs_grad_y = cv2.convertScaleAbs(grad_y)
        dst = cv2.addWeighted(abs_grad_x, 0.5, abs_grad_y, 0.5, 0)
        dst = cv2.convertScaleAbs(dst)
        img = cv2.addWeighted(img, 0.75, dst, 0.25, 0)
        img = cv2.convertScaleAbs(img)

    # applying sobel filter
    if sobel == 1:
        scale = 1
        delta = 0
        ddepth = cv2.CV_16S
        grad_x = cv2.Sobel(
            img,
            ddepth,
            1,
            0,
            ksize=3,
            scale=scale,
            delta=delta,
            borderType=cv2.BORDER_DEFAULT,
        )
        grad_y = cv2.Sobel(
            img,
            ddepth,
            0,
            1,
            ksize=3,
            scale=scale,
            delta=delta,
            borderType=cv2.BORDER_DEFAULT,
        )
        abs_grad_x = cv2.convertScaleAbs(grad_x)
        abs_grad_y = cv2.convertScaleAbs(grad_y)
        dst = cv2.addWeighted(abs_grad_x, 0.5, abs_grad_y, 0.5, 0)
        dst = cv2.convertScaleAbs(dst)
        img = cv2.addWeighted(img, 0.75, dst, 0.25, 0)
        img = cv2.convertScaleAbs(img)

    # applying laplacian filter
    if laplacian == 1:
        ddepth = cv2.CV_16S
        dst = cv2.Laplacian(img, ddepth, ksize=5)

        # dst = cv2.Canny(img, 100, 200); # canny edge detection test
        dst = cv2.convertScaleAbs(dst)
        img = cv2.addWeighted(img, 0.75, dst, 0.25, 0)
        img = cv2.convertScaleAbs(img)

    img_bin, ret = thresh_it(img, Threshtype, fg_color, asize, thresh)
    return img, img_bin, ret
