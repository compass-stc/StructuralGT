import numpy as np
import os
from StructuralGTEdits import error, base, process_image, convert, sknwEdits, util
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import time
import gsd.hoomd
from skimage.morphology import skeletonize_3d
from skimage.measure import regionprops, label
import copy

class PhysicalNetwork(util.Network):
    """A :class:`Network` class with methods for constructing networks from
    images. This is the parent class for all classes for which edges
    represent tangible links and should not be instantiated directly by the
    user.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def stack_to_gsd(
        self,
        name="skel.gsd",
        crop=None,
        skeleton=True,
        rotate=None,
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
                File name to write.
            crop (list):
                The x, y and (optionally) z coordinates of the cuboid/
                rectangle which encloses the :class:`Network` region of
                interest.
            skeleton (bool):
                Whether to write the skeleton or the unskeletonized
                binarization of the image(s).
            rotate (float):
                The amount to rotate the skeleton by *after* the
                :py:attr:`Gr` attribute has been set.
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
        if crop is not None and self.depth is None and not self._2d:
            if len(self.image_stack) < crop[5] - crop[4]:
                raise ValueError("Crop too large for image stack")
            else:
                self.depth = [crop[4], crop[5]]

        start = time.time()

        self.gsd_name = util._abs_path(self, name)
        self.gsd_dir = os.path.split(self.gsd_name)[0]

        if rotate is not None:
            self.inner_cropper = util._cropper(self, domain=crop)
            crop = self.inner_cropper._outer_crop

        self.set_img_bin(crop)
        
        if skeleton:
            self.skeleton = skeletonize_3d(np.asarray(self.img_bin, dtype=np.dtype('uint8')))
            self.skeleton_3d = skeletonize_3d(np.asarray(self.img_bin_3d, dtype=np.dtype('uint8')))
        else:
            self.img_bin = np.asarray(self.img_bin)
            self.skeleton_3d = self.img_bin_3d
            self.skeleton = self.img_bin

        positions = np.asarray(np.where(np.asarray(self.skeleton_3d) == 1)).T
        self.shape = np.asarray(
            list(max(positions.T[i]) + 1 for i in (2, 1, 0)[0 : self.dim])
        )
        self.positions = positions

        with gsd.hoomd.open(name=self.gsd_name, mode="w") as f:
            s = gsd.hoomd.Frame()
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

        # Until now, the rotation arguement has not been used; the image and
        # writted .gsds are all unrotated. The final block of this method is
        # for reassigning the image attribute, as well as setting the rotate
        # attribute for later. Only the img_bin attribute is altered because
        # the image_stack attribute exists to expose the unprocessed image to
        # the user.
        #
        # Also note that this only applies to 2D graphs, because 3D graphs
        # cannot be rotated.
        if rotate is not None:
            # Set the rotate attribute
            from scipy.spatial.transform import Rotation as R

            r = R.from_rotvec(rotate / 180 * np.pi * np.array([0, 0, 1]))
            self.rotate = r.as_matrix()
            self.crop = np.asarray(crop) - min(crop)
        else:
            self.rotate = None

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

        G = base.gsd_to_G(self.gsd_name, _2d=self._2d, sub=sub)

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
                if not base.isinside(np.asarray([node_positions[i]]), inner_crop):
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
                ), dtype=object
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

        if weight_type is not None:
            self.Gr = base.add_weights(self, weight_type=weight_type, **kwargs)

        self.shape = list(
            max(list(self.Gr.vs[i]["o"][j] for i in range(self.Gr.vcount())))
            for j in (0, 1, 2)[0 : self.dim]
        )

    def Node_labelling(self, attribute, label, filename, edge_weight=None, mode="r+"):
        """Method saves a new .gsd which labels the :attr:`Gr` attribute with
        the given node attribute values. Method saves the
        :class:`igraph.Graph` in the .gsd.

        Args:
            attribute (:class:`numpy.ndarray`):
                An array of attribute values in ascending order of node id.
            label (str):
                The label to give the attribute in the file.
            filename (str):
                The file name to write.
            edge_weight (optional, :class:`numpy.ndarray`):
                Any edge weights to store in the adjacency matrix.
            mode (optional, str):
                The writing mode.
        """
        if isinstance(self.Gr, list):
            self.Gr = self.Gr[0]

        assert self.Gr.vcount() == len(attribute)

        if filename[0] == "/":
            save_name = filename
        else:
            save_name = self.stack_dir + "/" + filename
        if mode == "r+" and os.path.exists(save_name):
            _mode = "r+"
        else:
            _mode = "w"

        f = gsd.hoomd.open(name=save_name, mode=_mode)
        self.labelled_name = save_name

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
        s = gsd.hoomd.Frame()
        N = len(positions)
        s.particles.N = N
        s.particles.position = positions
        s.particles.types = ["Edge", "Node"]
        s.particles.typeid = [0] * N
        s.configuration.box = [L[0] / 2, L[1] / 2, L[2] / 2, 0, 0, 0]
        s.log["particles/" + label] = [np.NaN] * N

        # Store adjacency matrix in CSR format
        matrix = self.Gr.get_adjacency_sparse(attribute=edge_weight)
        rows, columns = matrix.nonzero()
        values = matrix.data

        #rows, columns, values = convert.to_dense(
        #    np.array(self.Gr.get_adjacency(attribute=edge_weight).data, dtype=np.single)
        #)

        s.log["Adj_rows"] = rows
        s.log["Adj_cols"] = columns
        s.log["Adj_values"] = values

        j = 0
        for i, particle in enumerate(positions):
            node_id = np.where(np.all(positions[i] == node_positions, axis=1) == True)[
                0
            ]
            if len(node_id) == 0:
                continue
            else:
                s.log["particles/" + label][i] = attribute[node_id[0]]
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

    def bounded_betweenness(self, sources, targets, weights=None):
        from StructuralGTEdits import _bounded_betweenness_cast

        num_edges = self.Gr.ecount()
        _copy = copy.deepcopy(self.Gr)

        if weights is None:
            weights = np.ones(num_edges, dtype=np.double)
        else:
            weights = np.array(_copy.es[weights], dtype=np.double)

        cast = _bounded_betweenness_cast.PyCast(_copy._raw_pointer())

        cast.bounded_betweenness_compute(
            np.array(sources, dtype=np.longlong),
            np.array(targets, dtype=np.longlong),
            num_edges,
            weights,
        )

        return cast.bounded_betweenness

    def random_betweenness(self, sources, targets, weights=None):
        from StructuralGTEdits import _random_betweenness_cast

        num_edges = self.Gr.ecount()
        _copy = copy.deepcopy(self.Gr)

        if weights is None:
            weights = np.ones(num_edges, dtype=np.double)
        else:
            weights = np.array(_copy.es[weights], dtype=np.double)

        cast = _random_betweenness_cast.PyCast(_copy._raw_pointer())

        cast.random_betweenness_compute(
            np.array(sources, dtype=np.longlong),
            np.array(targets, dtype=np.longlong),
            num_edges,
            weights,
        )

        return cast.random_betweenness

    def nonlinear_random_betweenness(self, sources, targets, incoming,
                                     weights=None):
        from StructuralGTEdits import _nonlinear_random_betweenness_cast
        _copy = copy.deepcopy(self.Gr)

        #Add ghost node and edges from targets to ghost
        _copy.add_vertex(1)
        for target in targets:
            _copy.add_edge(self.Gr.vcount()-1,target)
        num_edges = _copy.ecount()

        #When passing weight vector, must add additional weights for edges
        #between targets and ghost node (added in cpp file)
        if weights is None:
            weights = np.ones(num_edges, dtype=np.double)
        else:
            mean = np.mean(np.array(self.Gr.es[weights]))

            weights = np.append(np.array(self.Gr.es[weights], dtype=np.double),
                                np.full(len(targets), mean, dtype=np.double)).astype(np.double)
            assert len(weights) == _copy.ecount()
        cast = _nonlinear_random_betweenness_cast.PyCast(_copy._raw_pointer())

        cast.nonlinear_random_betweenness_compute(
            np.array(sources, dtype=np.longlong),
            np.array(targets, dtype=np.longlong),
            np.array(incoming, dtype=np.longlong),
            num_edges,
            weights,
        )

        return cast.nonlinear_random_betweenness

    def average_nodal_connectivity(self):
        from StructuralGTEdits import _average_nodal_connectivity_cast
        _copy = copy.deepcopy(self.Gr)

        cast = _average_nodal_connectivity_cast.PyCast(_copy._raw_pointer())

        cast.average_nodal_connectivity_compute()

        return cast.average_nodal_connectivity

class ResistiveNetwork(PhysicalNetwork):
    """A :class:`Network` class with methods for analyzing flow in networks
    with linearly driven flow.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def potential_distribution(self, axis, boundary1, boundary2, R_j=0):
        """Solves for the potential distribution in a (optionally, weighted)
        network. Source and sink nodes are connected according to a
        penetration boundary condition. After calling, the weighted Laplacian,
        Laplacian pseudoinverse, potential and flow attributes (:attr:`L`,
        :attr:`Q`:, attr:`P`, :attr:`F`) are all set.

        Args:
            axis (int):
                The axis along which the boundary arguements refer to.
            boundary1 (list):
                The distances along axis in between which nodes will be
                connected to the source.
            boundary2 (list):
                The distances along axis in between which nodes will be
                connected to the sink.
            R_j (float, optional):
                The constant resistance term associated with each edge.

        NOTE: Critical that :meth:`G_u()` is called before every
        :meth:`potential_distribution()` call
        TODO: Remove this requirement or add an error to warn
        """

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
        indices = axes[axes != axis]
        axis_centre1 = np.zeros(self.dim, dtype=int)
        delta = np.zeros(self.dim, dtype=int)
        delta[axis] = 10  # Arbitrary. Standardize?
        for i in indices:
            axis_centre1[i] = self.shape[i] / 2
        axis_centre2 = np.copy(axis_centre1)
        axis_centre2[axis] = self.shape[axis]
        source_coord = axis_centre1 - delta
        sink_coord = axis_centre2 + delta
        print("source coord is ", source_coord)
        print("sink coord is ", sink_coord)
        self.Gr_connected.vs[source_id]["o"] = source_coord
        self.Gr_connected.vs[sink_id]["o"] = sink_coord

        print(
            "Before connecting external nodes, G has vcount ",
            self.Gr_connected.vcount(),
        )
        for node in self.Gr_connected.vs:
            if node["o"][axis] >= boundary1[0] and node["o"][axis] <= boundary1[1]:
                self.Gr_connected.add_edges([(node.index, source_id)])
                self.Gr_connected.es[self.Gr_connected.get_eid(node.index, source_id)][
                    "Conductance"
                ] = weight_avg
                self.Gr_connected.es[self.Gr_connected.get_eid(node.index, source_id)][
                    "pts"
                ] = base.connector(source_coord, node["o"])
            if node["o"][axis] >= boundary2[0] and node["o"][axis] <= boundary2[1]:
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
        base.G_to_gsd(self.Gr_connected, connected_name)

        if R_j == "infinity":
            self.L = np.asarray(self.Gr.laplacian())
        else:
            self.L = np.asarray(self.Gr.laplacian(weights="Conductance"))

        F = np.zeros(sink_id + 1)
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


class StructuralNetwork(PhysicalNetwork):
    """A :class:`Network` class with methods for analyzing classical network
    structural parameters.
    """

    def __init__(self, directory, *args, **kwargs):
        super().__init__(directory, *args, **kwargs)

    def G_calc(self):
        """Assigns :attr:`G_attributes` as a dictionary with values of the
        graph's diameter, density, undirected transitivity and assortativity
        (by degree).
        """

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
        """Calculates nodewise parameters of the graph and assigns them as
        attribute to the :class:`Network` object.

        Args:
            Betweenness (bool, optional):
                Whether to calculate node betweenness.
            Closeness (bool, optional):
                Whether to calculate node closeness.
            Degree (bool, optional):
                Whether to calculate node degree.
        """
        if not isinstance(self.Gr, list):
            self.Gr = [self.Gr]

        self.Betweenness = []
        self.Closeness = []
        self.Degree = []
        for graph in self.Gr:
            if Betweenness:
                self.Betweenness.append(graph.betweenness(directed=False))
            if Closeness:
                self.Closeness.append(graph.closeness())
            if Degree:
                self.Degree.append(graph.degree())


class StructuralNetworkList(StructuralNetwork):
    """[IN PROGRESS]
    Class for analyzing images of disconnected networks, where each
    network is a discreet object of interest. :attr:`Gr` is a list of
    standard :class:`StructuralNetwork` objects.
    """

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
            raise ValueError("NetworkLists cannot be rotated")

    def __len__(self):
        return len(self.Gr)
