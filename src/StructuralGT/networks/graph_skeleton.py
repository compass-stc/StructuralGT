# SPDX-License-Identifier: GNU GPL v3

"""
Create a graph skeleton from an image binary
"""

import math
import numpy as np
from scipy import ndimage
from cv2.typing import MatLike
from skimage.morphology import binary_dilation as dilate, binary_closing
from skimage.morphology import disk, skeletonize, remove_small_objects


class GraphSkeleton:
    """A class that is used for estimating the width of edges and compute their weights using binerized 2D/3D images."""

    def __init__(self, img_bin: MatLike, configs: dict = None, is_2d: bool = True, progress_func = None):
        """
        A class that builds a skeleton graph from an image.
        The skeleton will be 3D so that it can be analyzed with OVITO

        :param img_bin: OpenCV image in binary format.
        :param configs: Options and parameters.

        >>> import cv2
        >>> import numpy
        >>> opt_gte = {}
        >>> opt_gte["merge_nearby_nodes"]["value"] = 1
        >>> opt_gte["remove_disconnected_segments"]["value"] = 1
        >>> opt_gte["remove_object_size"]["value"] = 500
        >>> opt_gte["prune_dangling_edges"]["value"] = 1
        >>> dummy_image = 127 * numpy.ones((40, 40), dtype = np.uint8)
        >>> img = cv2.threshold(dummy_image, 127, 255, cv2.THRESH_BINARY)[1]
        >>> graph_skel = GraphSkeleton(img, opt_gte)

        """
        self.img_bin = img_bin
        self.configs = configs
        self.is_2d = is_2d
        self.update_progress = progress_func
        self.skeleton, self.skeleton_3d = None, None
        if configs is not None:
            self._build_skeleton()

    def _build_skeleton(self):
        """
        Creates a graph skeleton of the image.

        :return:
        """

        # rebuilding the binary image as a boolean for skeletonizing
        self.img_bin = np.squeeze(self.img_bin)
        img_bin_int = np.asarray(self.img_bin, dtype=np.uint16)

        # making the initial skeleton image
        temp_skeleton = skeletonize(img_bin_int)

        # Use medial axis with distance transform
        # skeleton, distance = medial_axis(img_bin_int, return_distance=True)
        # Scale thickness by distance (optional)
        # temp_skeleton = skeleton * distance

        # if self.configs["remove_bubbles"]["value"] == 1:
        #    temp_skeleton = GraphSkeleton.remove_bubbles(temp_skeleton, img_bin_int, mask_elements)
            # if self.update_progress is not None:
            # self.update_progress([56, f"Ran remove_bubbles for image skeleton..."])

        if self.configs["merge_nearby_nodes"]["value"] == 1:
            node_radius_size = 2 # int(self.configs["merge_nearby_nodes"]["items"][0]["value"])
            temp_skeleton = GraphSkeleton.merge_nodes(temp_skeleton, node_radius_size)
            if self.update_progress is not None:
                self.update_progress([52, f"Ran merge_nodes for image skeleton..."])

        if self.configs["remove_disconnected_segments"]["value"] == 1:
            min_size = int(self.configs["remove_disconnected_segments"]["items"][0]["value"])
            temp_skeleton = remove_small_objects(temp_skeleton, min_size=min_size, connectivity=2)
            if self.update_progress is not None:
                self.update_progress([54, f"Ran remove_small_objects for image skeleton..."])

        if self.configs["prune_dangling_edges"]["value"] == 1:
            max_iter = 500 # int(self.configs["prune_dangling_edges"]["items"][0]["value"])
            b_points = GraphSkeleton.get_branched_points(temp_skeleton)
            temp_skeleton = GraphSkeleton.prune_edges(temp_skeleton, max_iter, b_points)
            if self.update_progress is not None:
                self.update_progress([56, f"Ran prune_dangling_edges for image skeleton..."])

        self.skeleton = np.asarray(temp_skeleton, dtype=np.uint16)
        # self.skeleton = self.skeleton.astype(int)
        self.skeleton_3d = np.asarray([self.skeleton]) if self.is_2d else self.skeleton

    def assign_weights(self, edge_pts: MatLike, weight_type: str = None, weight_options: dict = None,
                       pixel_dim: float = 1, rho_dim: float = 1):
        """
        Compute and assign weights to a line edge between 2 nodes.

        :param edge_pts: A list of pts that trace along a graph edge.
        :param weight_type: Basis of computation for the weight (i.e., length, width, resistance, conductance, etc.)
        :param weight_options: weight types to be used in computation of weights.
        :param pixel_dim: Physical size of a single pixel width in nanometers.
        :param rho_dim: The resistivity value of the material.
        :return: Width pixel count of edge, computed weight.
        """

        # Initialize parameters: Idea copied from 'sknw' library
        pix_length = np.linalg.norm(edge_pts[1:] - edge_pts[:-1], axis=1).sum()
        epsilon = 0.001             # to avoid division by zero
        pix_length += epsilon

        if len(edge_pts) < 2:
            # check to see if ge is an empty or unity list, if so, set pixel counts to 0
            # Assume only 1/2 pixel exists between edge points
            pix_width = 0.5
            pix_angle = None
        else:
            # if ge exists, find the midpoint of the trace, and orthogonal unit vector
            pix_width, pix_angle = self._estimate_edge_width(edge_pts)
            pix_width += 0.5  # (normalization) to make it larger than empty widths

        if weight_type is None:
            wt = pix_width / 10
        elif weight_options.get(weight_type) == weight_options.get('DIA'):
            wt = pix_width * pixel_dim
        elif weight_options.get(weight_type) == weight_options.get('AREA'):
            wt = math.pi * (pix_width * pixel_dim * 0.5) ** 2
        elif weight_options.get(weight_type) == weight_options.get('LEN') or weight_options.get(weight_type) == weight_options.get('INV_LEN'):
            wt = pix_length * pixel_dim
            if weight_options.get(weight_type) == weight_options.get('INV_LEN'):
                wt = wt + epsilon if wt == 0 else wt
                wt = wt ** -1
        elif weight_options.get(weight_type) == weight_options.get('ANGLE'):
            """
            Edge angle centrality" in graph theory refers to a measure of an edge's importance within a network, 
            based on the angles formed between the edges connected to its endpoints, essentially assessing how "central" 
            an edge is in terms of its connection to other edges within the network, with edges forming more acute 
            angles generally considered more central. 
            To calculate edge angle centrality, you would typically:
               1. For each edge, identify the connected edges at its endpoints.
               2. Calculate the angles between these connected edges.
               3. Assign a higher centrality score to edges with smaller angles, indicating a more central position in the network structure.
            """
            sym_angle = np.minimum(pix_angle, (360 - pix_angle))
            wt = (sym_angle + epsilon) ** -1
        elif weight_options.get(weight_type) == weight_options.get('FIX_CON') or weight_options.get(weight_type) == weight_options.get('VAR_CON') or weight_options.get(weight_type) == weight_options.get('RES'):
            # Varies with width
            length = pix_length * pixel_dim
            area = math.pi * (pix_width * pixel_dim * 0.5) ** 2
            if weight_options.get(weight_type) == weight_options.get('FIX_CON'):
                area = math.pi * (1 * pixel_dim) ** 2
            num = length * rho_dim
            area = area + epsilon if area == 0 else area
            num =  num + epsilon if num == 0 else num
            wt = (num / area)  # Resistance
            if weight_options.get(weight_type) == weight_options.get('VAR_CON') or weight_options.get(weight_type) == weight_options.get('FIX_CON'):
                wt = wt ** -1  # Conductance is inverse of resistance
        else:
            raise TypeError('Invalid weight type')
        return pix_width, pix_angle, wt

    def _estimate_edge_width(self, graph_edge_coords: MatLike):
        """Estimates the edge width of a graph edge."""

        def find_orthogonal(u, v):
            # Inputs:
            # u, v: two coordinates (x, y) or (x, y, z)
            vec = u - v  # find the vector between u and v

            if np.linalg.norm(vec) == 0:
                n = np.array([0, ] * len(u), dtype=np.float16)
            else:
                # make n a unit vector along u,v
                n = vec / np.linalg.norm(vec)

            hl = np.linalg.norm(vec) / 2  # find the half-length of the vector u,v
            ortho_arr = np.random.randn(len(u))  # take a random vector
            ortho_arr -= ortho_arr.dot(n) * n  # make it orthogonal to vector u,v
            ortho_arr /= np.linalg.norm(ortho_arr)  # make it a unit vector

            # Returns the coordinates of the vector u,v midpoint; the orthogonal unit vector
            return (v + n * hl), ortho_arr

            # 1. Estimate orthogonal and mid-point
        end_index = len(graph_edge_coords) - 1
        pt1 = graph_edge_coords[0]
        pt2 = graph_edge_coords[end_index]
        # mid_index = int(len(graph_edge_coords) / 2)
        # mid_pt = graph_edge_coords[mid_index]

        mid_pt, ortho = find_orthogonal(pt1, pt2)
        # mid: the midpoint of a trace of an edge
        # ortho: an orthogonal unit vector
        mid_pt = mid_pt.astype(int)

        # 2. Compute the angle in Radians
        # Delta X and Y: Compute the difference in x and y coordinates:
        dx = pt2[0] - pt1[0]
        dy = pt2[1] - pt1[1]
        # Angle Calculation: Use the arc-tangent function to get the angle in radians:
        angle_rad = math.atan2(dy, dx)
        angle_deg = math.degrees(angle_rad)
        if angle_deg < 0:
            angle_deg += 360

        # 3. Estimate width
        check = 0  # initializing boolean check
        i = 0      # initializing iterative variable
        l1 = np.nan
        l2 = np.nan
        while check == 0:             # iteratively check along orthogonal vector to see if the coordinate is either...
            pt_check = mid_pt + i * ortho  # ... out of bounds, or no longer within the fiber in img_bin
            pt_check = pt_check.astype(int)
            is_in_edge = GraphSkeleton.point_check(self.img_bin, pt_check)

            if is_in_edge:
                edge = mid_pt + (i - 1) * ortho
                edge = edge.astype(int)
                l1 = edge  # When the check indicates oob or black space, assign width to l1
                check = 1
            else:
                i += 1

        check = 0
        i = 0
        while check == 0:  # Repeat, but following the negative orthogonal vector
            pt_check = mid_pt - i * ortho
            pt_check = pt_check.astype(int)
            is_in_edge = GraphSkeleton.point_check(self.img_bin, pt_check)

            if is_in_edge:
                edge = mid_pt - (i - 1) * ortho
                edge = edge.astype(int)
                l2 = edge  # When the check indicates oob or black space, assign width to l2
                check = 1
            else:
                i += 1

        # returns the length between l1 and l2, which is the width of the fiber associated with an edge, at its midpoint
        edge_width = np.linalg.norm(l1 - l2)
        return edge_width, angle_deg

    @classmethod
    def _generate_transformations(cls, pattern):
        """
        Generate common transformations for a pattern.

         * flipud is flipping them up-down
         * t_branch_2 is t_branch_0 transposed, which permutes it in all directions (might not be using that word right)
         * t_branch_3 is t_branch_2 flipped left right
         * those 3 functions are used to create all possible branches with just a few starting arrays below

        :param pattern: Pattern of the box as a numpy array.

        """
        return [
            pattern,
            np.flipud(pattern),
            np.fliplr(pattern),
            np.fliplr(np.flipud(pattern)),
            pattern.T,
            np.flipud(pattern.T),
            np.fliplr(pattern.T),
            np.fliplr(np.flipud(pattern.T))
        ]

    @classmethod
    def get_branched_points(cls, skeleton: MatLike):
        """Identify and retrieve the branched points from the graph skeleton."""
        skel_int = skeleton * 1

        # Define base patterns
        base_patterns = [
            [[1, 0, 1], [0, 1, 0], [1, 0, 1]],  # x_branch
            [[0, 1, 0], [1, 1, 1], [0, 1, 0]],  # x_branch variant
            [[0, 0, 0], [1, 1, 1], [0, 1, 0]],  # t_branch
            [[1, 0, 1], [0, 1, 0], [1, 0, 0]],  # t_branch variant
            [[1, 0, 1], [0, 1, 0], [0, 1, 0]],  # y_branch
            [[0, 1, 0], [1, 1, 0], [0, 0, 1]],  # y_branch variant
            [[0, 1, 0], [1, 1, 0], [1, 0, 1]],  # off_branch
            [[0, 1, 1], [0, 1, 1], [1, 0, 0]],  # clust_branch
            [[1, 1, 1], [0, 1, 1], [1, 0, 0]],  # clust_branch variant
            [[1, 1, 1], [0, 1, 1], [1, 0, 1]],  # clust_branch variant
            [[1, 0, 0], [1, 1, 1], [0, 1, 0]]  # cross_branch
        ]

        # Generate all transformations
        all_patterns = []
        for pattern in base_patterns:
            all_patterns.extend(cls._generate_transformations(np.array(pattern)))

        # Remove duplicate patterns (if any)
        unique_patterns = []
        for pattern in all_patterns:
            if not any(np.array_equal(pattern, existing) for existing in unique_patterns):
                unique_patterns.append(pattern)

        # Apply binary hit-or-miss for all unique patterns
        br = sum(ndimage.binary_hit_or_miss(skel_int, pattern) for pattern in unique_patterns)
        return br

    @classmethod
    def get_end_points(cls, skeleton: MatLike):
        """
        Identify and retrieve the end points from the graph skeleton.
        """
        skel_int = skeleton * 1

        # List of endpoint patterns
        endpoints = [
            [[0, 0, 0], [0, 1, 0], [0, 1, 0]],
            [[0, 0, 0], [0, 1, 0], [0, 0, 1]],
            [[0, 0, 0], [0, 1, 1], [0, 0, 0]],
            [[0, 0, 1], [0, 1, 0], [0, 0, 0]],
            [[0, 1, 0], [0, 1, 0], [0, 0, 0]],
            [[1, 0, 0], [0, 1, 0], [0, 0, 0]],
            [[0, 0, 0], [1, 1, 0], [0, 0, 0]],
            [[0, 0, 0], [0, 1, 0], [1, 0, 0]],
            [[0, 0, 0], [0, 1, 0], [0, 0, 0]]
        ]

        # Apply binary hit-or-miss for each pattern and sum results
        ep = sum(ndimage.binary_hit_or_miss(skel_int, np.array(pattern)) for pattern in endpoints)
        return ep

    @classmethod
    def prune_edges(cls, skeleton: MatLike, max_num, branch_points):
        """Prune dangling edges around b_points. Remove iteratively end points 'size' times from the skeleton"""
        temp_skeleton = skeleton.copy()
        for i in range(0, max_num):
            end_points = GraphSkeleton.get_end_points(temp_skeleton)
            points = np.logical_and(end_points, branch_points)
            end_points = np.logical_xor(end_points, points)
            end_points = np.logical_not(end_points)
            temp_skeleton = np.logical_and(temp_skeleton, end_points)
        return temp_skeleton

    @classmethod
    def merge_nodes(cls, skeleton: MatLike, node_radius):
        """Merge nearby nodes in the graph skeleton."""
        # overlay a disk over each branch point and find the overlaps to combine nodes
        skeleton_int = 1 * skeleton
        mask_elem = disk(node_radius)
        bp_skel = GraphSkeleton.get_branched_points(skeleton)
        bp_skel = 1 * (dilate(bp_skel, mask_elem))

        # wide-nodes is initially an empty image the same size as the skeleton image
        skel_shape = skeleton_int.shape
        wide_nodes = np.zeros(skel_shape, dtype='int')

        # this overlays the two skeletons
        # skeleton_integer is the full map, bp_skel is just the branch points blown up to a larger size
        for x in range(skel_shape[0]):
            for y in range(skel_shape[1]):
                if skeleton_int[x, y] == 0 and bp_skel[x, y] == 0:
                    wide_nodes[x, y] = 0
                else:
                    wide_nodes[x, y] = 1

        # re-skeletonizing wide-nodes and returning it, nearby nodes in radius 2 of each other should have been merged
        temp_skeleton = skeletonize(wide_nodes)
        return temp_skeleton

    @classmethod
    def remove_bubbles(cls, img_bin: MatLike, mask_elements: list):
        """Remove bubbles from graph skeleton."""
        if not isinstance(mask_elements, list):
            return None

        canvas = img_bin.copy()
        for mask_elem in mask_elements:
            canvas = skeletonize(mask_elem)
            canvas = binary_closing(canvas, footprint=mask_elem)

        temp_skeleton = skeletonize(canvas)
        return temp_skeleton

    @staticmethod
    def point_check(img_bin: MatLike, pt_check):
        """Checks and verifies that a point is on a graph edge."""

        def boundary_check(coord, w, h, d=None):
            """

            Args:
                coord: the coordinate (x,y) to check; no (x,y,z) compatibility yet.
                w: width of the image to set the boundaries.
                h: the height of the image to set the boundaries.
                d: the depth of the image to set the boundaries.
            Returns:

            """
            out_of_bounds = 0  # Generate a boolean check for out-of-boundary
            # Check if coordinate is within the boundary
            if d is None:
                if coord[0] < 0 or coord[1] < 0 or coord[-2] > (w - 1) or coord[-1] > (h - 1):
                    out_of_bounds = 1
            else:
                # if sum(coord < 0) > 0 or sum(coord > [w - 1, h - 1, d - 1]) > 0:
                if sum(coord < 0) > 0 or coord[-3] > (d - 1) or coord[-2] > (w - 1) or coord[-1] > (h - 1):
                    out_of_bounds = 1

            # returns the boolean oob (1 if there is a boundary error); coordinates (resets to (1,1) if boundary error)
            return out_of_bounds

        # Check if the image is 2D
        if len(img_bin.shape) == 2:
            is_2d = True
            height, width = img_bin.shape  # finds dimensions of img_bin for boundary check
            depth = 0
        else:
            is_2d = False
            depth, height, width = img_bin.shape

        try:
            if is_2d:
                # Checks if the point in fiber is out-of-bounds (oob) or black space (img_bin(x,y) = 0)
                oob = boundary_check(pt_check, width, height)
                not_in_edge = True if (oob == 1) else True if (img_bin[pt_check[-2], pt_check[-1]] == 0) else False
            else:
                # Checks if the point in fiber is out-of-bounds (oob) or black space (img_bin(d,x,y) = 0)
                oob = boundary_check(pt_check, width, height, d=depth)
                not_in_edge = True if (oob == 1) else True if (img_bin[pt_check[-3], pt_check[-2], pt_check[-1]] == 0) else False
        except IndexError:
            not_in_edge = True
        return not_in_edge
