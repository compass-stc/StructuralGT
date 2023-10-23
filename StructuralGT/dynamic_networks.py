import numpy as np
import os
import cv2 as cv
from StructuralGT import error, base, process_image, convert, sknwEdits, util
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import gsd.hoomd
from skimage.morphology import skeletonize_3d
import copy

class DynamicNetwork(util.Network):
    """A :class:`Network` class with methods for the analysis of 
    user.
    """
    def write_slices(self, video, child_dir, depth):


        video_dir = os.path.split(video)[0]
        stack_dir = video_dir + '/' + child_dir
        # Path to video file
        vidObj = cv.VideoCapture(video)

        # Used as counter variable
        count = 0
        domain = util._domain(depth)

        # checks whether frames were extracted
        success = True

        while success:
            if count >= domain.domain[0] and count <= domain.domain[1]:
                # vidObj object calls read
                # function extract frames
                success, image = vidObj.read()
                # Saves the frames with frame-count
                cv.imwrite(video_dir + "/slice" + base.quadrupletise(count) + ".tiff", image)
            else:
                success = False
            count += 1

    def __init__(self, video, child_dir="Binarized", depth=None, **kwargs):
        self.write_slices(video, child_dir, depth)
        directory = os.path.split(video)[0]
        super().__init__(directory, **kwargs)

    def img_to_skel(
        self,
        name="skel.gsd",
        crop=None,
        skeleton=True,
        debubble=None,
        box=False,
        merge_nodes=None,
        prune=None,
        remove_objects=None,
    ):

        """Writes a .gsd file from the object's directory. The name of the
        written .gsd is set as an attribute so it may be easily matched with
        its :class:`igraph.Graph` object. Running this also sets the
        positions, shape attributes.

        Note: if the rotation argument is given, this writes the union of all
        of the graph which can be obtained from cropping after rotation (i.e.
        that which is returned by self.crop._outer_crop). The rotated skeleton
        can be written after the :py:attr:`Gr` attribute has been set.

        Args:
            name (str):
                Filename prefix to write.
            crop (list):
                The x, y and (optionally) z coordinates of the cuboid/
                rectangle which encloses the :class:`Network` region of
                interest.
            skeleton (bool):
                Whether to write the skeleton or the unskeletonized
                binarization of the image(s).
            debubble (list[:class:`numpy.ndarray`]):
                The footprints to use for a debubbling protocol.
            box (bool):
                Whether to plot the boundaries of the cropped
                :class:`Network`.
            merge_nodes (int):
                The radius of the disk used in the node merging protocol,
                taken from :cite:`Vecchio2021`.
            prune (int):
                The number of times to apply the pruning algorithm taken from
                :cite:`Vecchio2021`.
            remove_objects (int):
                The size of objects to remove from the skeleton, using the
                algorithm in :cite:`Vecchio2021`.
        """

        self.gsd_prefix = util._abs_path(self, name)[:-4] #Drop '.gsd'
        self.gsd_dir = os.path.split(self.gsd_prefix)[0]

        self.set_img_bin(crop)
        
        if skeleton:
            self.skeleton = skeletonize_3d(np.asarray(self.img_bin, dtype=np.dtype('uint8')))
            self.skeleton_3d = skeletonize_3d(np.asarray(self.img_bin_3d, dtype=np.dtype('uint8')))
        else:
            self.img_bin = np.asarray(self.img_bin)
            self.skeleton_3d = self.img_bin_3d
            self.skeleton = self.img_bin

        i=0
        for _ in self.image_stack:
            positions = np.asarray(np.where(np.asarray(self.skeleton_3d[i]) == 1)).T
            self.shape = np.asarray(
                list(max(positions.T[i]) + 1 for i in (1,0))
            )
            self.positions = positions

            with gsd.hoomd.open(name=self.gsd_prefix+str(i)+'.gsd', mode="w") as f:
                s = gsd.hoomd.Frame()
                s.particles.N = len(positions)
                if box:
                    L = list(max(positions.T[i]) for i in (0, 1, 2))
                    s.particles.position, self.shift = base.shift(
                        positions, _shift=(L[0] / 2, L[1] / 2, L[2] / 2)
                    )
                    s.configuration.box = [L[0], L[1], L[2], 0, 0, 0]
                else:
                    s.particles.position, self.shift = base.shift(positions,
                                                                  _2d=True)
                s.particles.types = ["A"]
                s.particles.typeid = ["0"] * s.particles.N
                f.append(s)

            print(
                "Ran stack_to_gsd() in ",
                end - start,
                "for gsd with ",
                len(positions),
                "particles",
            )

            if debubble is not None:
                self = base.debubble(self, debubble)

            if merge_nodes is not None:
                self = base.merge_nodes(self, merge_nodes)

            if prune is not None:
                self = base.prune(self, prune)

            if remove_objects is not None:
                self = base.remove_objects(self, remove_objects)

    def G_u(self, sub=True, weight_type=None, **kwargs):
        """Sets :class:`igraph.Graph` object as an attribute by reading the
        skeleton file written by :meth:`stack_to_gsd`.

        Args:
            sub (optional, bool):
                Whether to onlyh assign the largest connected component as the
                :class:`igraph.Graph` object.
            weight_type (optional, str):
                How to weight the edges. Options include 'Length', 'Width',
                'Area', 'FixedWidthConductance', 'VariableWidthConductance'.
        """

        self.Gr = []
        for i in self.image_stack:
            G = base.gsd_to_G(self.gsd_prefix+str(i)+'.gsd', _2d=True, sub=sub)
            
            if weight_type is not None:
                G = base.add_weights(self, weight_type=weight_type, **kwargs)
            
            self.Gr.append(G)

        self.shape = list(
            max(list(self.Gr.vs[i]["o"][j] for i in range(self.Gr.vcount())))
            for j in (0, 1, 2)[0 : self.dim]
        )

