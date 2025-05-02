
import os
import io
import csv
import base64

import cv2
import gsd.hoomd
import numpy as np
import multiprocessing as mp
import matplotlib.pyplot as plt
from PIL import Image
from typing import LiteralString
from cv2.typing import MatLike


def get_num_cores():
    """
    Finds the count of CPU cores in a computer or a SLURM supercomputer.
    :return: Number of cpu cores (int)
    """
    num_cores = __get_slurm_cores__()
    if not num_cores:
        num_cores = mp.cpu_count()
    return num_cores


def __get_slurm_cores__():
    """
    Test the computer to see if it is a SLURM environment, then gets the number of CPU cores.
    :return: Count of CPUs (int) or False
    """
    try:
        cores = int(os.environ['SLURM_JOB_CPUS_PER_NODE'])
        return cores
    except ValueError:
        try:
            str_cores = str(os.environ['SLURM_JOB_CPUS_PER_NODE'])
            temp = str_cores.split('(', 1)
            cpus = int(temp[0])
            str_nodes = temp[1]
            temp = str_nodes.split('x', 1)
            str_temp = str(temp[1]).split(')', 1)
            nodes = int(str_temp[0])
            cores = cpus * nodes
            return cores
        except ValueError:
            return False
    except KeyError:
        return False


def write_txt_file(data: str, path: LiteralString | str | bytes, wr=True):
    """Description
        Writes data into a txt file.

        :param data: Information to be written
        :param path: name of the file and storage path
        :param wr: writes data into file if True
        :return:
    """
    if wr:
        with open(path, 'w') as f:
            f.write(data)
            f.close()
    else:
        pass


def write_csv_file(csv_file: LiteralString | str | bytes, column_tiles: list, data):
    """
    Write data to a csv file.
    Args:
        csv_file: name of the csv file
        column_tiles: list of column names
        data: list of data
    Returns:

    """
    with open(csv_file, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile, delimiter=',')
        writer.writerow(column_tiles)
        for line in data:
            line = str(line)
            row = line.split(',')
            try:
                writer.writerow(row)
            except csv.Error:
                pass
    csvfile.close()


def write_gsd_file(f_name: str, skeleton: np.ndarray):
    """
    A function that writes graph particles to a GSD file. Visualize with OVITO software.

    :param f_name: gsd.hoomd file name
    :param skeleton: skimage.morphology skeleton
    """
    # pos_count = int(sum(skeleton.ravel()))
    particle_positions = np.asarray(np.where(np.asarray(skeleton) != 0)).T
    with gsd.hoomd.open(name=f_name, mode="w") as f:
        s = gsd.hoomd.Frame()
        s.particles.N = len(particle_positions)  # OR pos_count
        s.particles.position = particle_positions
        s.particles.types = ["A"]
        s.particles.typeid = ["0"] * s.particles.N
        f.append(s)


def img_to_base64(img: MatLike | Image.Image):
    """ Converts a Numpy/OpenCV or PIL image to a base64 encoded string."""
    if img is None:
        return None

    if type(img) == np.ndarray:
        return opencv_to_base64(img)

    if type(img) == Image.Image:
        # Convert to numpy, apply safe conversion
        np_img = np.array(img)
        img_norm = safe_uint8_image(np_img)
        return opencv_to_base64(img_norm)

    return None


def opencv_to_base64(img_arr: MatLike):
    """Convert an OpenCV/Numpy image to a base64 string."""
    success, encoded_img = cv2.imencode('.png', img_arr)
    if success:
        buffer = io.BytesIO(encoded_img.tobytes())
        buffer.seek(0)
        base64_data = base64.b64encode(buffer.getvalue()).decode("utf-8")
        return base64_data
    else:
        return None


def plot_to_opencv(fig: plt.Figure):
    """Convert a Matplotlib figure to an OpenCV BGR image (Numpy array), retaining colors."""
    if fig:
        buf = io.BytesIO()
        fig.savefig(buf, format='png', bbox_inches='tight')
        buf.seek(0)

        # Convert bytes to a Numpy array
        img_array = np.frombuffer(buf.getvalue(), dtype=np.uint8)
        buf.close()

        # Decode image as BGR (color), discard alpha channel
        img_cv = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
        return img_cv
    return None


def safe_uint8_image(img: MatLike):
    """
    Converts an image to uint8 safely:
        - If already uint8, returns as is.
        - If float or other type, normalizes to 0–255 and converts to uint8.
    """
    if img.dtype == np.uint8:
        return img

    # Handle float or other types
    min_val = np.min(img)
    max_val = np.max(img)

    if min_val == max_val:
        # Avoid divide by zero; return constant grayscale
        return np.full(img.shape, 0 if min_val == 0 else 255, dtype=np.uint8)

    # Normalize to 0–255
    norm_img = ((img - min_val) / (max_val - min_val)) * 255.0
    return norm_img.astype(np.uint8)