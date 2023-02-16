#import sknwEdits as sknw
import numpy as np
import os
import cv2 as cv
from StructuralGTEdits import error, base, process_image, convert, sknwEdits
import json
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import time
import gsd.hoomd
from skimage.morphology import skeletonize_3d, disk, binary_dilation
from skimage.measure import regionprops, label
import copy

def _dir_reader(Network):
    """Function returns effective depth, dimension and first name of
    directory belonging to a particular Network object.

    """
    
    olist = np.asarray(sorted(os.listdir(Network.stack_dir)))
    mask = list(base.Q_img(olist[i]) for i in range(len(olist)))
    fname = sorted(olist[mask])[0]  # First name

    return fname

def _abs_path(network, name):
    if name[0] == "/":
        return name
    else:
        return network.stack_dir + "/" + name

def _outer_crop(crop):
    # Calculate outer crop
    # (i.e. that which could contain any rotation of the inner crop)
    # Use it to write the unrotated skel.gsd
    centre = (
        crop[0] + 0.5 * (crop[1] - crop[0]),
        crop[2] + 0.5 * (crop[3] - crop[2]),
    )

    diagonal = ((crop[1] - crop[0]) ** 2 + (crop[3] - crop[2]) ** 2) ** 0.5

    outer_crop = np.array(
        [
            centre[0] - diagonal * 0.5,
            centre[0] + diagonal * 0.5,
            centre[1] - diagonal * 0.5,
            centre[1] + diagonal * 0.5,
        ],
        dtype=int,
    )

    return outer_crop


class _cropper:
    """Crop object: contains methods to deal with images of different
    dimensions etc. Should not be instnatiated directly.


    dim is dimensions: 2 or 3
    dims is lengths: eg (500,1500,10)
    crop is crop point locations eg (x1,x2,y1,y2,z1,z2)
    
    Requires a Network object for instantiation, in order to determine
    network depth and number of dimensions

    As is the case in all directory reading, depth is determined from 
    the number of image files in Network.stack_dir
    """

    def __init__(self, Network, domain=None):
        self.dim = Network.dim
        if domain is None or Network._2d:
            self.surface = int(
                _fname(Network.dir + '/' + Network.slice_names[0]).num
            )  # Strip file type and 'slice' then convert to int
        else:
            self.surface = domain[4]
        if Network._2d:
            self.depth = 1
        else:
            if domain is None:
                self.depth = len(Network.slice_names)
            else:
                self.depth = domain[5] - domain[4]
            if self.depth == 0:
                raise error.ImageDirectoryError(Network.stack_dir)

        # Assign dims and crop
        if domain is None:
            self.crop = slice(None)
            planar_dims = cv.imread(
                Network.stack_dir + "/slice000.tiff",
                cv.IMREAD_GRAYSCALE).shape
            if self.dim == 2:
                self.dims = (1,) + planar_dims
            else:
                self.dims = (self.depth,) + planar_dims

        else:
            if self.dim == 2:
                self.crop = (slice(domain[2], domain[3]),
                             slice(domain[0], domain[1]))
                self.dims = (1, domain[3] - domain[2], domain[1] - domain[0])

            else:
                self.crop = (
                    slice(domain[0], domain[1]),
                    slice(domain[2], domain[3]),
                    slice(domain[4], domain[5]),
                )
                self.dims = (
                    domain[1] - domain[0],
                    domain[3] - domain[2],
                    domain[5] - domain[4],
                )

    def _2d(self):
        if self.crop == slice(None):
            return slice(None)
        else:
            return self.crop[0:2]

    def intergerise(self):
        first_x = np.floor(self.crop[0].start).astype(int)
        last_x = np.ceil(self.crop[0].stop).astype(int)

        first_y = np.floor(self.crop[1].start).astype(int)
        last_y = np.ceil(self.crop[1].stop).astype(int)

        if self.dim == 2:
            self.crop = slice(first_x, last_x), slice(first_y, last_y)
            self.dims = (1, last_x - first_x, last_y - first_y)
        else:
            first_z = np.floor(self.crop[2].start).astype(int)
            last_z = np.ceil(self.crop[2].stop).astype(int)
            self.crop = (
                slice(first_x, last_x),
                slice(first_y, last_y),
                slice(first_z, last_z),
            )


class _domain():

    def __init__(self, domain):
        if domain is None:
            self.domain = [-np.inf, np.inf]
        else:
            self.domain = domain


class _fname():
    """Assumes each file has 3 character number
    Eg 053, followed by 3 or 4 character extension
    extension Eg .tif or .tiff
    """

    def __init__(self, name, domain=_domain(None)):
        if not os.path.exists(name):
            raise ValueError('File does not exist')
        self.name = name
        self.domain = domain
        num1 = name[-7:-4]
        num2 = name[-8:-5]
        if num1.isnumeric() and num2.isnumeric():
            raise ValueError('Directory contents names ambiguous')
        elif num1.isnumeric():
            self.num = num1
        elif num2.isnumeric():
            self.num = num2
        else:
            self.num = 'Non-numeric'

    def isnumeric(self):
        return self.num.isnumeric()

    def inrange(self):
        if not self.isnumeric():
            return False
        else:
            return (int(self.num) > self.domain.domain[0]
                    and int(self.num) < self.domain.domain[1])

    def isimg(self):
        return base.Q_img(self.name)


class Network:
    """Generic SGT graph class: a specialised case of the igraph Graph object with
    additional attributes defining geometric features, associated images,
    dimensionality etc.

    Initialised from directory containing raw image data
    self._2d determined from the number of images with identical dimensions
    (suggesting a stack when > 1)

    Image shrinking/cropping is carried out at the gsd stage in analysis.
    I.e. full images are binarized but cropping their graphs may come after

    crop arguement for 3D networks only, (a,b)
    """

    def __init__(self, directory, child_dir="/Binarized",
                 depth=None):
        if not isinstance(directory, str):
            raise TypeError

        self.dir = directory
        self.child_dir = child_dir
        self.stack_dir = self.dir + self.child_dir
        self.rotate = None

        self.Q = None
        self.depth = depth
        self.crop = None

        self.img, self.slice_names = [], []
        for slice_name in sorted(os.listdir(self.dir)):
            fname = _fname(self.dir + '/' + slice_name,
                           domain=_domain(depth))
            if (fname.inrange() and fname.isimg()):
                _slice = cv.imread(self.dir + "/" + slice_name,
                                   cv.IMREAD_GRAYSCALE)
                self.img.append(_slice)
                self.slice_names.append(slice_name)

        self.img = np.asarray(self.img)
        if len(self.slice_names) == 1:
            self._2d = True
            self.dim = 2
        else:
            self._2d = False
            self.dim = 3

    def binarize(self, options_dict=None):
        """Binarizes stack of experimental images using a set of image processing
        parameters in options_dict. Note this enforces that all images have the
        same shape as the first image encountered by the for loop.
        (i.e. the first alphanumeric titled image file)
        """

        if options_dict is None:
            options = self.dir + "/img_options.json"
            with open(options) as f:
                options_dict = json.load(f)

        if not os.path.isdir(self.dir + self.child_dir):
            os.mkdir(self.dir + self.child_dir)

        i = 0
        for name in self.slice_names:
            fname = _fname(self.dir + '/' + name)
            img_exp = cv.imread(self.dir + "/" + name, cv.IMREAD_GRAYSCALE)
            _, img_bin, _ = process_image.binarize(img_exp, options_dict)
            plt.imsave(
                self.stack_dir + "/slice" + fname.num + ".tiff",
                img_bin,
                cmap=cm.gray,
            )
            i += 1

        self.options = options_dict

    def stack_to_gsd(self, name="skel.gsd", crop=None, skeleton=True,
                     rotate=None, debubble=None, box=False, merge_nodes=None,
                     prune=None, remove_objects=None):

        """Writes a .gsd file from the object's directory.
        The name of the written .gsd is set as an attribute so it may be
        easily matched with its Graph object
        Running this also sets the positions, shape attributes.

        Note: if the rotation argument is given, this writes the union of all
        of the graph which can be obtained from cropping after rotation.
        """
        if not self._2d and rotate is not None:
            raise ValueError("Cannot rotate 3D graphs.")
        if crop is None and rotate is not None:
            raise ValueError("If rotating a graph, crop must be specified")
        if crop is not None and self.depth is not None:
            if crop[4] < self.depth[0] or crop[5] > self.depth[1]:
                raise ValueError(
                    "crop argument cannot be outwith the bounds of \
                    the network's depth"
                )
        start = time.time()

        self.gsd_name = _abs_path(self, name)
        self.gsd_dir = os.path.split(self.gsd_name)[0]

        if rotate is not None:
            self.inner_cropper = _cropper(self, domain=crop)
            crop = _outer_crop(crop)

        self.cropper = _cropper(self, domain=crop)

        # Initilise i such that it starts at the lowest number belonging
        # to the images in the stack_dir
        # First require boolean mask to filter out non image files
        if self._2d:
            img_bin = np.zeros(self.cropper.dims)
        else:
            img_bin = np.zeros(self.cropper.dims)
            # img_bin = np.swapaxes(img_bin, 1, 2)

        i = self.cropper.surface
        for fname in sorted(os.listdir(self.stack_dir)):
            fname = _fname(self.stack_dir + '/' + fname, domain=_domain(self.depth))
            if fname.isnumeric() and fname.inrange():
                suff = base.tripletise(i)
                img_bin[i - self.cropper.surface] = (
                    base.read(
                        self.stack_dir + "/slice" + fname.num + ".tiff",
                        cv.IMREAD_GRAYSCALE,
                    )[self.cropper._2d()]
                    / 255
                )
                i = i + 1
            else:
                continue

        # For 2D images, img_bin_3d.shape[0] == 1
        self.img_bin_3d = img_bin
        self.img_bin = img_bin

        # Always 3d, even for 2d images
        self.img_bin_3d = self.img_bin
        # 3d for 3d images, 2d otherwise
        self.img_bin = np.squeeze(self.img_bin)

        if skeleton:
            self.skeleton = skeletonize_3d(np.asarray(self.img_bin, dtype=int))
            self.skeleton_3d = skeletonize_3d(np.asarray(self.img_bin_3d, dtype=int))
        else:
            self.img_bin = np.asarray(self.img_bin)
            self.skeleton_3d = self.img_bin_3d
            self.skeleton = self.img_bin

        positions = np.asarray(np.where(np.asarray(self.skeleton_3d) == 1)).T
        self.shape = np.asarray(
            list(max(positions.T[i]) + 1 for i in (2, 1, 0)[0 : self.dim])
        )
        self.positions = positions

        with gsd.hoomd.open(name=self.gsd_name, mode="wb") as f:
            s = gsd.hoomd.Snapshot()
            s.particles.N = len(positions)
            if box:
                L = list(max(positions.T[i]) for i in (0, 1, 2))
                s.particles.position, self.shift = base.shift(
                    positions, _shift=(L[0] / 2, L[1] / 2, L[2] / 2)
                )
                s.configuration.box = [L[0], L[1], L[2], 0, 0, 0]
            else:
                s.particles.position, self.shift = base.shift(positions)
            s.particles.types = ["A"]
            s.particles.typeid = ["0"] * s.particles.N
            f.append(s)

        end = time.time()
        print(
            "Ran stack_to_gsd() in ", end - start, "for gsd with ",
            len(positions), "particles",
        )

        if debubble is not None:
            self = base.debubble(self, debubble)

        if merge_nodes is not None:
            self = base.merge_nodes(self, merge_nodes)

        if prune is not None:
            self = base.prune(self, prune)

        if remove_objects is not None:
            self = base.remove_objects(self, remove_objects)

        """Set rot matrix attribute for later"""
        if rotate is not None:
            from scipy.spatial.transform import Rotation as R

            r = R.from_rotvec(rotate / 180 * np.pi * np.array([0, 0, 1]))
            self.rotate = r.as_matrix()
            self.crop = np.asarray(crop) - min(crop)

    def G_u(self, **kwargs):
        """
        Sets igraph object as an attribute
        When rotate!=None, the initial graph is the outer crop,
        obtained from the written .gsd
        """
        if "merge_size" not in kwargs:
            kwargs["merge_size"] = None
        if "sub" not in kwargs:
            kwargs["sub"] = True

        G = base.gsd_to_G(self.gsd_name, _2d=self._2d, sub=kwargs["sub"])

        self.Gr = G

        if self.rotate is not None:
            centre = np.asarray(self.shape) / 2
            inner_length_x = (self.inner_cropper.dims[2]) * 0.5
            inner_length_y = (self.inner_cropper.dims[1]) * 0.5
            inner_crop = np.array(
                [
                    centre[0] - inner_length_x,
                    centre[0] + inner_length_x,
                    centre[1] - inner_length_y,
                    centre[1] + inner_length_y,
                ],
                dtype=int,
            )

            node_positions = np.asarray(
                list(self.Gr.vs[i]["o"] for i in range(self.Gr.vcount()))
            )
            node_positions = base.oshift(node_positions, _shift=centre)
            node_positions = np.vstack(
                (node_positions.T, np.zeros(len(node_positions)))
            ).T
            node_positions = np.matmul(node_positions, self.rotate).T[0:2].T
            node_positions = base.shift(node_positions, _shift=-centre)[0]

            drop_list = []
            for i in range(self.Gr.vcount()):
                if not base.Q_inside(np.asarray([node_positions[i]]), inner_crop):
                    drop_list.append(i)
                    continue

                self.Gr.vs[i]["o"] = node_positions[i]
                self.Gr.vs[i]["pts"] = node_positions[i]
            self.Gr.delete_vertices(drop_list)

            node_positions = np.asarray(
                list(self.Gr.vs[i]["o"] for i in range(self.Gr.vcount()))
            )
            final_shift = np.asarray(
                list(min(node_positions.T[i]) for i in (0, 1, 2)[0 : self.dim])
            )
            edge_positions_list = np.asarray(
                list(
                    base.oshift(self.Gr.es[i]["pts"], _shift=centre)
                    for i in range(self.Gr.ecount())
                )
            )
            for i, edge in enumerate(edge_positions_list):
                edge_position = np.vstack((edge.T, np.zeros(len(edge)))).T
                edge_position = np.matmul(edge_position, self.rotate).T[0:2].T
                edge_position = base.shift(edge_position, _shift=-centre + final_shift)[
                    0
                ]
                self.Gr.es[i]["pts"] = edge_position

            node_positions = base.shift(node_positions, _shift=final_shift)[0]
            for i in range(self.Gr.vcount()):
                self.Gr.vs[i]["o"] = node_positions[i]
                self.Gr.vs[i]["pts"] = node_positions[i]

        if kwargs["merge_size"]:
            print("Calling self.merge()")
            G = self.merge_nodes(kwargs["merge_size"])
            self.Gr = base.sub_G(G)

        if len(kwargs) != 0:
            if "sub" in kwargs:
                kwargs.pop("sub")
            if "merge_size" in kwargs:
                kwargs.pop("merge_size")
            if "weight_type" in kwargs:
                self.Gr = base.add_weights(self, **kwargs)

        self.shape = list(
            max(list(self.Gr.vs[i]["o"][j] for i in range(self.Gr.vcount())))
            for j in (0, 1, 2)[0 : self.dim]
        )

    def weighted_Laplacian(self, weights="weight"):

        L = np.asarray(self.Gr.laplacian(weights=weights))
        self.L = L

    def Node_labelling(
        self, attribute, attribute_name, filename, edge_weight=None, mode="rb+"
    ):
        """
        Method saves a new .gsd which has the graph in self.Gr labelled
        with the node attributes in attribute. Method saves all the main
        attributes of a Network object in the .gsd such that the network
        object may be loaded from the file
        """
        if isinstance(self.Gr, list):
            self.Gr = self.Gr[0]

        assert self.Gr.vcount() == len(attribute)

        if filename[0] == "/":
            save_name = filename
        else:
            save_name = self.stack_dir + "/" + filename
        if mode == "rb+" and os.path.exists(save_name):
            _mode = "rb+"
        else:
            _mode = "wb"

        f = gsd.hoomd.open(name=save_name, mode=_mode)
        self.labelled_name = save_name

        # Must segregate position list into a node_position and edge_position
        node_positions = np.asarray(
            list(self.Gr.vs()[i]["o"] for i in range(self.Gr.vcount()))
        )
        positions = node_positions
        for edge in self.Gr.es():
            positions = np.vstack((positions, edge["pts"]))
        positions = np.unique(positions, axis=0)
        if self._2d:
            node_positions = np.hstack(
                (np.zeros((len(node_positions), 1)), node_positions)
            )
            positions = np.hstack((np.zeros((len(positions), 1)), positions))

        L = list(max(positions.T[i]) * 2 for i in (0, 1, 2))
        node_positions = base.shift(
            node_positions, _shift=(L[0] / 4, L[1] / 4, L[2] / 4)
        )[0]
        positions = base.shift(positions, _shift=(L[0] / 4, L[1] / 4, L[2] / 4))[0]
        s = gsd.hoomd.Snapshot()
        N = len(positions)
        s.particles.N = N
        s.particles.position = positions
        s.particles.types = ["Edge", "Node"]
        s.particles.typeid = [0] * N
        s.configuration.box = [L[0] / 2, L[1] / 2, L[2] / 2, 0, 0, 0]
        # s.configuration.box = [1, 1, 1, 0, 0, 0]
        s.log["particles/" + attribute_name] = [np.NaN] * N

        # To store graph, must first convert sparse adjacency
        # matrix as 3 dense matrices
        rows, columns, values = convert.to_dense(
            np.array(self.Gr.get_adjacency(attribute=edge_weight).data, dtype=np.single)
        )
        s.log["Adj_rows"] = rows
        s.log["Adj_cols"] = columns
        s.log["Adj_values"] = values
        # s.log['img_options'] = self.options

        # Store optional Network attributes
        # if self.Q is not None: s.log['InvLaplacian'] = self.Q

        j = 0
        for i, particle in enumerate(positions):
            node_id = np.where(np.all(positions[i] == node_positions, axis=1) == True)[
                0
            ]
            if len(node_id) == 0:
                continue
            else:
                s.log["particles/" + attribute_name][i] = attribute[node_id[0]]
                s.particles.typeid[i] = 1
                j += 1

        f.append(s)

    def recon(self, axis, surface, depth):
        """Method displays 2D slice of binary image and
        annotates with attributes from 3D graph subslice
        """

        Gr_copy = copy.deepcopy(self.Gr)

        # self.Gr = base.sub_G(self.Gr)

        axis_0 = abs(axis - 2)

        display_img = np.swapaxes(self.img_bin_3d, 0, axis_0)[surface]
        drop_list = []
        for i in range(self.Gr.vcount()):
            if (
                self.Gr.vs[i]["o"][axis_0] < surface
                or self.Gr.vs[i]["o"][axis_0] > surface + depth
            ):
                drop_list.append(i)
                continue

        self.Gr.delete_vertices(drop_list)

        node_positions = np.asarray(
            list(self.Gr.vs()[i]["o"] for i in range(self.Gr.vcount()))
        )
        positions = np.array([[0, 0, 0]])
        for edge in self.Gr.es():
            positions = np.vstack((positions, edge["pts"]))

        fig = plt.figure(figsize=(10, 25))
        plt.scatter(node_positions.T[2], node_positions.T[1], s=10, color="red")
        plt.scatter(positions.T[2], positions.T[1], s=2)
        plt.imshow(self.img_bin[axis], cmap=cm.gray)
        plt.show()

        self.Gr = Gr_copy

    def merge_nodes(self, merge_size):
        """
        Currently deos not rewrite merged .gsd
        Also does not reset skeleton attribute
        Should it?
        """
        if self.rotate is None:
            cropper = self.cropper
        else:
            cropper = self.inner_cropper
        cropper.intergerise()
        canvas = np.zeros(
            np.ceil(cropper.dims[1:3]).astype(int) + (1,) * self.dim, dtype=int
        )
        pos = np.asarray(
            list(self.Gr.vs[i]["o"] for i in range(self.Gr.vcount())), dtype=int
        )
        canvas[pos.T[0], pos.T[1]] = 1
        canvas = binary_dilation(canvas, merge_size)

        binary = np.ceil(
            (
                self.skeleton[0 : cropper.dims[1], 0 : cropper.dims[2]]
                + canvas[0 : cropper.dims[1], 0 : cropper.dims[2]]
            )
            / 2
        ).astype(int)
        new_skel = skeletonize_3d(binary)
        G = sknwEdits.build_sknw(new_skel.astype(int))

        return G

    def bounded_betweenness(self, sources, targets, weights=None):
        from StructuralGTEdits import _bounded_betweenness_cast

        num_edges = self.Gr.ecount()
        _copy = copy.deepcopy(self.Gr)
        
        if weights is None:
            weights = np.ones(num_edges, dtype=np.double)
        else:
            weights = np.array(_copy.es[weights])

        cast = _bounded_betweenness_cast.PyCast(_copy._raw_pointer())

        cast.bounded_betweenness_compute(np.array(sources), np.array(targets),
                                         num_edges, weights)

        return cast.bounded_betweenness

class ResistiveNetwork(Network):
    """Child of generic SGT Network class.
    Equipped with methods for analysing resistive flow networks
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def potential_distribution(self, plane, boundary1, boundary2, R_j=0, rho_dim=1):
        """
        Solves for the potential distribution in a weighted network.
        Source and sink nodes are connected according to a penetration boundary condition.
        Sets the corresponding weighted Laplacian, potential and flow attributes.
        The 'plane' arguement defines the axis along which the boundary arguements refer to.
        R_j='infinity' enables the unusual case of all edges having the same unit resistance.

        NOTE: Critical that self.G_u() is called before every self.potential_distribution() call
        TODO: Remove this requirement or add an error to warn
        """
        # self.G_u(weight_type=['Conductance'], R_j=R_j, rho_dim=rho_dim) #Assign weighted graph attribute
        # self.Gr = base.sub_G(self.Gr)

        self.Gr_connected = self.Gr
        if R_j != "infinity":
            weight_array = np.asarray(self.Gr.es["Conductance"]).astype(float)
            weight_array = weight_array[~np.isnan(weight_array)]
            self.edge_weights = weight_array
            weight_avg = np.mean(weight_array)
        else:
            self.Gr_connected.es["Conductance"] = np.ones(self.Gr.ecount())
            weight_avg = 1

        # Add source and sink nodes:
        source_id = max(self.Gr_connected.vs).index + 1
        sink_id = source_id + 1
        self.Gr_connected.add_vertices(2)

        print("Graph has max ", self.shape)
        axes = np.array([0, 1, 2])[0 : self.dim]
        indices = axes[axes != plane]
        plane_centre1 = np.zeros(self.dim, dtype=int)
        delta = np.zeros(self.dim, dtype=int)
        delta[plane] = 10  # Arbitrary. Standardize?
        for i in indices:
            plane_centre1[i] = self.shape[i] / 2
        plane_centre2 = np.copy(plane_centre1)
        plane_centre2[plane] = self.shape[plane]
        source_coord = plane_centre1 - delta
        sink_coord = plane_centre2 + delta
        print("source coord is ", source_coord)
        print("sink coord is ", sink_coord)
        self.Gr_connected.vs[source_id]["o"] = source_coord
        self.Gr_connected.vs[sink_id]["o"] = sink_coord

        # Connect nodes on a given boundary to the external current nodes
        print(
            "Before connecting external nodes, G has vcount ",
            self.Gr_connected.vcount(),
        )
        for node in self.Gr_connected.vs:
            if node["o"][plane] >= boundary1[0] and node["o"][plane] <= boundary1[1]:
                self.Gr_connected.add_edges([(node.index, source_id)])
                self.Gr_connected.es[self.Gr_connected.get_eid(node.index, source_id)][
                    "Conductance"
                ] = weight_avg
                self.Gr_connected.es[self.Gr_connected.get_eid(node.index, source_id)][
                    "pts"
                ] = base.connector(source_coord, node["o"])
            if node["o"][plane] >= boundary2[0] and node["o"][plane] <= boundary2[1]:
                self.Gr_connected.add_edges([(node.index, sink_id)])
                self.Gr_connected.es[self.Gr_connected.get_eid(node.index, sink_id)][
                    "Conductance"
                ] = weight_avg
                self.Gr_connected.es[self.Gr_connected.get_eid(node.index, sink_id)][
                    "pts"
                ] = base.connector(sink_coord, node["o"])

        # Write skeleton connected to external node
        print(self.Gr_connected.is_connected(), " connected")
        print(
            "After connecting external nodes, G has vcount ", self.Gr_connected.vcount()
        )
        connected_name = (
            os.path.split(self.gsd_name)[0]
            + "/connected_"
            + os.path.split(self.gsd_name)[1]
        )
        # connected_name = self.stack_dir + '/connected_' + self.gsd_name
        base.G_to_gsd(self.Gr_connected, connected_name)

        if R_j == "infinity":
            self.L = np.asarray(self.Gr.laplacian())
        else:
            self.weighted_Laplacian(weights="Conductance")

        F = np.zeros(sink_id + 1)
        print(self.L.shape, "L")
        F[source_id] = 1
        F[sink_id] = -1

        Q = np.linalg.pinv(self.L, hermitian=True)
        P = np.matmul(Q, F)

        self.P = P
        self.F = F
        self.Q = Q

    def effective_resistance(self, source=-1, sink=-2):

        O_eff = self.Q[source, source] + self.Q[sink, sink] - 2 * self.Q[source, sink]

        return O_eff


class StructuralNetwork(Network):
    """
    Child of generic SGT Network class.
    Equipped with methods for analysing structural networks
    """

    def __init__(self, directory, *args, **kwargs):
        super().__init__(directory, *args, **kwargs)

    def G_calc(self):
        avg_indices = dict()

        operations = [
            self.Gr.diameter,
            self.Gr.density,
            self.Gr.transitivity_undirected,
            self.Gr.assortativity_degree,
        ]
        names = ["Diameter", "Density", "Clustering", "Assortativity by degree"]

        for operation, name in zip(operations, names):
            start = time.time()
            avg_indices[name] = operation()
            end = time.time()
            print("Calculated ", name, " in ", end - start)

        self.G_attributes = avg_indices

    def node_calc(self, Betweenness=True, Closeness=True, Degree=True):
        if not isinstance(self.Gr, list):
            self.Gr = [self.Gr]

        self.Betweenness = []
        self.Closeness = []
        self.Degree = []
        for graph in self.Gr:
            if Betweenness:
                self.Betweenness.append(graph.betweenness())
            if Closeness:
                self.Closeness.append(graph.closeness())
            if Degree:
                self.Degree.append(graph.degree())

    
class StructuralNetworkVector(StructuralNetwork):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def G_u(self, **kwargs):
        label_img = label(self.img_bin)
        regions = regionprops(label_img)

        self.Gr = []
        for props in regions:
            minr, minc, maxr, maxc = props.bbox
            crop = list(
                np.asarray([minr, maxr, minc, maxc])
                - np.asarray(
                    [
                        self.shift[0][1],
                        self.shift[0][1],
                        self.shift[0][2],
                        self.shift[0][2],
                    ]
                )
            )
            self.Gr.append(
                base.gsd_to_G(self.gsd_name, _2d=self._2d, sub=False, crop=crop)
            )

        if self.rotate is not None:
            raise ValueError("NetworkVectors cannot be rotated")

        if len(kwargs) != 0:
            if "sub" in kwargs:
                kwargs.pop("sub")
            if "merge_size" in kwargs:
                kwargs.pop("merge_size")
            if "weight_type" in kwargs:
                self.Gr = base.add_weights(self, **kwargs)

    def __len__(self):
        return len(self.Gr)
