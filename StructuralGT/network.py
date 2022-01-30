#Draft
import numpy as np
import igraph as ig
import os
import cv2 as cv
from StructuralGT import base, process_image, error
import json
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import time
import functools
import gsd.hoomd
from skimage.morphology import skeletonize_3d, disk
import pandas as pd

class Network():
    """Generic SGT graph class: a specialised case of the igraph Graph object with 
    additional attributes defining geometric features, associated images,
    dimensionality etc.
    
    Initialised from directory containing raw image data
    self._2d determined from the number of images with identical dimensions (suggesting a stack when > 1)
    
    Image shrinking/cropping is carried out at the gsd stage in analysis.
    I.e. full images are binarized but cropping their graphs may come after
    """
    def __init__(self, directory, child_dir='/Binarized'):
        if not isinstance(directory, str):
            raise TypeError
            
        self.dir = directory
        self.child_dir = child_dir
        self.stack_dir = self.dir + self.child_dir
        
        shape = []
        for name in sorted(os.listdir(self.dir)):
            if not base.Q_img(name):
                continue
            shape.append(cv.imread(self.dir+'/'+name,cv.IMREAD_GRAYSCALE).shape)
        
        if len(set(shape)) == len(shape):
            self._2d = True
            self.dim = 2
        else:
            self._2d = False
            self.dim = 3
        
    def binarize(self, options_dict=None):
        """Binarizes stack of experimental images using a set of image processing parameters in options_dict.
        Note this enforces that all images have the same shape as the first image encountered by the for loop.
        (i.e. the first alphanumeric titled image file)
        """
        
        if options_dict is None:
            options = self.dir + '/img_options.json'
            with open(options) as f:
                options_dict = json.load(f)

        if not os.path.isdir(self.dir + self.child_dir):
            os.mkdir(self.dir + self.child_dir)

        i=0
        for name in sorted(os.listdir(self.dir)):
            if not base.Q_img(name):
                continue
            else:
                img_exp = cv.imread(self.dir+'/'+name,cv.IMREAD_GRAYSCALE)
                if i == 0: shape = img_exp.shape
                elif img_exp.shape != shape: continue
                _, img_bin, _ = process_image.binarize(img_exp, options_dict)
                plt.imsave(self.dir+self.child_dir+'/slice'+str(i)+'.tiff', img_bin, cmap=cm.gray)
                i+=1
        
    def stack_to_gsd(self, name='skel.gsd', crop=None, skeleton=True, rotate=None, debubble=None):
        """Writes a .gsd file from the object's directory.
        The name of the written .gsd is set as an attribute so it may be easily matched with its Graph object 
        Running this also sets the positions, shape attributes
        
        For 2D graphs, the first element of the 3D position list is all 0s. So the gsd y corresponds to the graph
        x and the gsd z corresponds to the graph y.

        """
        start = time.time()
        
        if name[0] == '/':
            self.gsd_name = name
        else:
            self.gsd_name = self.stack_dir + '/' + name
        self.gsd_dir = os.path.split(self.gsd_name)[0]
        img_bin=[]

        #Initilise i such that it starts at the lowest number belonging to the images in the stack_dir
        #First require boolean mask to filter out non image files
        olist = np.asarray(sorted(os.listdir(self.stack_dir)))
        mask = list(base.Q_img(olist[i]) for i in range(len(olist)))
        if len(mask) == 0:
            raise error.ImageDirectoryError(self.stack_dir)
        fname = sorted(olist[mask])[0] #First name
        i = int(os.path.splitext(fname)[0][5:]) #Strip file type and 'slice' then convert to int

        #Generate 3d (or 2d) array from stack
        for fname in sorted(os.listdir(self.stack_dir)):
            if base.Q_img(fname):
                img_slice = cv.imread(self.stack_dir+'/slice'+str(i)+'.tiff',cv.IMREAD_GRAYSCALE)
                if rotate is not None:
                    image_center = tuple(np.array(img_slice.shape[1::-1]) / 2)
                    rot_mat = cv.getRotationMatrix2D(image_center, rotate, 1.0)
                    img_slice = cv.warpAffine(img_slice, rot_mat, img_slice.shape[1::-1], flags=cv.INTER_LINEAR)
                img_bin.append(img_slice)
                i=i+1
            else:
                continue

        #For 2D images, img_bin_3d.shape[0] == 1
        img_bin = np.asarray(img_bin)
        self.img_bin_3d = img_bin
        self.img_bin = img_bin

        #Note that numpy array slicing operations are carried out in reverse order!
        #(...hence crop 2 and 3 before 0 and 1)
        if crop and self._2d:
            self.img_bin = self.img_bin[:, crop[2]:crop[3], crop[0]:crop[1]]
            #img_bin = img_bin[crop[0]:crop[1], crop[2]:crop[3]]
        elif crop:
            #TODO figure tf this bit out
            self.img_bin = self.img_bin[crop[0]:crop[1], crop[2]:crop[3], crop[4]:crop[5]]

        assert self.img_bin_3d.shape[1] > 1
        assert self.img_bin_3d.shape[2] > 1
        
        self.img_bin_3d = self.img_bin            #Always 3d, even for 2d images
        self.img_bin = np.squeeze(self.img_bin)   #3d for 3d images, 2d otherwise

        assert self.img_bin_3d.shape[1] == self.img_bin.shape[0]
        assert self.img_bin_3d.shape[2] == self.img_bin.shape[1]
        
        if skeleton:
            self.skeleton = skeletonize_3d(np.asarray(self.img_bin))
            self.skeleton_3d = skeletonize_3d(np.asarray(self.img_bin_3d))
            #self.skeleton_3d = np.swapaxes(self.skeleton_3d, 1, 2)
        else:
            self.img_bin = np.asarray(self.img_bin)

        positions = np.asarray(np.where(np.asarray(self.skeleton_3d) == 255)).T
        self.shape = np.asarray(list(max(positions.T[i])+1 for i in (0,1,2)[0:self.dim]))
        self.positions = positions

        print(positions)
        print(self.img_bin.shape)

        with gsd.hoomd.open(name=self.gsd_name, mode='wb') as f:
            s = gsd.hoomd.Snapshot()
            s.particles.N = len(positions)
            s.particles.position = base.shift(positions)
            s.particles.types = ['A']
            s.particles.typeid = ['0']*s.particles.N
            f.append(s)

        end = time.time()
        print('Ran stack_to_gsd() in ', end-start, 'for gsd with ', len(positions), 'particles')

        if debubble is not None: self = base.debubble(self, debubble)

        assert self.img_bin.shape == self.skeleton.shape
        assert self.img_bin_3d.shape == self.skeleton_3d.shape

        
    def stack_to_circular_gsd(self, radius, name='circle.gsd', rotate=None, debubble=None, skeleton=True):
        """Writes a cicular .gsd file from the object's directory.
        Currently only capable of 2D graphs
        Unlike stack_to_gsd, the axis of rotation is not the centre of the image, but the point (radius,radius)
        The name of the written .gsd is set as an attribute so it may be easily matched with its Graph object 
        Running this also sets the positions, shape attributes
        """
        start = time.time()
        if name[0] == '/':
            self.gsd_name = name
        else:
            self.gsd_name = self.stack_dir + '/' + name
        self.gsd_dir = os.path.split(self.gsd_name)[0]
        img_bin=[]
        
        #Initilise i such that it starts at the lowest number belonging to the images in the stack_dir
        #First require boolean mask to filter out non image files
        olist = np.asarray(sorted(os.listdir(self.stack_dir)))
        mask = list(base.Q_img(olist[i]) for i in range(len(olist)))
        if len(mask) == 0:
            raise error.ImageDirectoryError(self.stack_dir)
        fname = sorted(olist[mask])[0] #First name
        i = int(os.path.splitext(fname)[0][5:]) #Strip file type and 'slice' then convert to int
        
        img_slice = cv.imread(self.stack_dir+'/slice'+str(i)+'.tiff',cv.IMREAD_GRAYSCALE)
        
        #Read the image
        for fname in sorted(os.listdir(self.stack_dir)):
            if base.Q_img(fname):
                img_slice = cv.imread(self.stack_dir+'/slice'+str(i)+'.tiff',cv.IMREAD_GRAYSCALE)
                if rotate is not None:
                    axis_of_rot = tuple((radius,radius))
                    #image_center = tuple(np.array(img_slice.shape[1::-1]) / 2)
                    rot_mat = cv.getRotationMatrix2D(axis_of_rot, rotate, 1.0)
                    img_slice = cv.warpAffine(img_slice, rot_mat, img_slice.shape[1::-1], flags=cv.INTER_LINEAR)
                img_bin.append(img_slice)
                i=i+1
            else:
                continue
                
        #For 2D images, img_bin_3d.shape[0] == 1
        img_bin = np.asarray(img_bin)
        
        self.img_bin_3d = img_bin            #Always 3d, even for 2d images
        self.img_bin = np.squeeze(img_bin)   #3d for 3d images, 2d otherwise
        
        #Note that numpy array slicing operations are carried out in reverse order!
        #(...hence crop 2 and 3 before 0 and 1)
        assert self._2d


        canvas = np.ones(self.img_bin.shape)
        disk_pos = np.asarray(np.where(disk(radius)!=0)).T
        canvas[disk_pos[0], disk_pos[1]] = 0
        self.img_bin = np.ma.MaskedArray(self.img_bin, mask=canvas)
        self.img_bin = np.ma.filled(self.img_bin, fill_value=0)
        
        canvas = np.ones(self.img_bin_3d.shape)
        disk_pos = np.asarray(np.where(disk(radius)!=0)).T
        disk_pos = np.array([np.zeros(len(disk_pos)), disk_pos.T[0], disk_pos.T[1]], dtype=int)
        canvas[disk_pos[0], disk_pos[1], disk_pos[2]] = 0
        self.img_bin_3d = np.ma.MaskedArray(self.img_bin_3d, mask=canvas)
        self.img_bin_3d = np.ma.filled(self.img_bin_3d, fill_value=0)
        self.img_bin = self.img_bin_3d[0]
        
        assert self.img_bin_3d.shape[1] > 1
        assert self.img_bin_3d.shape[2] > 1
        
        if skeleton:
            self.skeleton = skeletonize_3d(np.asarray(self.img_bin))
            self.skeleton_3d = skeletonize_3d(np.asarray(self.img_bin_3d))
        else:
            self.img_bin = np.asarray(self.img_bin)
        
        positions = np.asarray(np.where(np.asarray(self.skeleton_3d) == 255)).T
        self.shape = np.asarray(list(max(positions.T[i])+1 for i in (0,1,2)[0:self.dim]))
        self.positions = positions
        
        with gsd.hoomd.open(name=self.gsd_name, mode='wb') as f:
            s = gsd.hoomd.Snapshot()
            s.particles.N = len(positions)
            s.particles.position = base.shift(positions)
            s.particles.types = ['A']
            s.particles.typeid = ['0']*s.particles.N
            f.append(s)
        
        end = time.time()
        print('Ran stack_to_gsd() in ', end-start, 'for gsd with ', len(positions), 'particles')
        
        if debubble is not None: self = base.debubble(self, debubble)
            
        assert self.img_bin.shape == self.skeleton.shape
        assert self.img_bin_3d.shape == self.skeleton_3d.shape    
        
        
    def G_u(self):
        """Sets unweighted igraph object as an attribute
        """
        G =  base.gsd_to_G(self.gsd_name, _2d = self._2d)
        self.Gr = G
        self.shape = list(max(list(self.Gr.vs[i]['o'][j] for i in range(self.Gr.vcount()))) for j in (0,1,2)[0:self.dim])
        
    def weighted_Laplacian(self):

        L=np.asarray(self.Gr.laplacian(weights='weight'))
        self.L = L

class ResistiveNetwork(Network):
    """Child of generic SGT Network class.
    Equipped with methods for analysing resistive flow networks

    """
    def __init__(self, directory):
        super().__init__(directory)
        
    def potential_distribution(self, plane, boundary1, boundary2, R_j=0, rho_dim=1, F_dim=1):
        """Solves for the potential distribution in a weighted network.
        Source and sink nodes are connected according to a penetration boundary condition.
        Sets the corresponding weighted Laplacian, potential and flow attributes.
        The 'plane' arguement defines the axis along which the boundary arguements refer to.
        R_j='infinity' enables the unusual case of all edges having the same unit resistance.
        
        NOTE: Critical that self.G_u() is called before every self.potential_distribution()
        TODO: Remove this requirement or add an error to warn
        """
        self.Gr = base.sub_G(self.Gr)
        print('post sub has ', self.Gr.vcount(), ' nodes')
        if R_j != 'infinity':
            print(self.Gr.vcount())
            self.Gr_connected = base.add_weights(self, weight_type='Conductance', R_j=R_j, rho_dim=rho_dim)
            print(self.Gr.vcount())
            weight_array = np.asarray(self.Gr_connected.es['weight']).astype(float)
            weight_array = weight_array[~np.isnan(weight_array)]
            self.edge_weights = weight_array
            weight_avg =np.mean(weight_array)
        else:
            self.Gr_connected = self.Gr
            self.Gr_connected.es['weight'] = np.ones(self.Gr_connected.ecount())
            weight_avg = 1

        #Add source and sink nodes:
        source_id = max(self.Gr_connected.vs).index + 1
        sink_id = source_id + 1
        self.Gr_connected.add_vertices(2)

        print('Graph has max ', self.shape)
        axes = np.array([0,1,2])[0:self.dim]
        indices = axes[axes!=plane]
        plane_centre1 = np.zeros(self.dim, dtype=int)
        delta = np.zeros(self.dim, dtype=int)
        delta[plane] = 10 #Arbitrary. Standardize?
        for i in indices: plane_centre1[i] = self.shape[i]/2
        plane_centre2 = np.copy(plane_centre1)
        plane_centre2[plane] = self.shape[plane]
        source_coord = plane_centre1 - delta 
        sink_coord = plane_centre2 + delta
        print('source coord is ', source_coord)
        print('sink coord is ', sink_coord)
        self.Gr_connected.vs[source_id]['o'] = source_coord
        self.Gr_connected.vs[sink_id]['o'] = sink_coord

    #Connect nodes on a given boundary to the external current nodes
        print('Before connecting external nodes, G has vcount ', self.Gr_connected.vcount())
        for node in self.Gr_connected.vs:
            if node['o'][plane] > boundary1[0] and node['o'][plane] < boundary1[1]:
                self.Gr_connected.add_edges([(node.index, source_id)])
                self.Gr_connected.es[self.Gr_connected.get_eid(node.index,source_id)]['weight'] = weight_avg
                self.Gr_connected.es[self.Gr_connected.get_eid(node.index,source_id)]['pts'] = base.connector(source_coord,node['o'])
            if node['o'][plane] > boundary2[0] and node['o'][plane] < boundary2[1]:
                self.Gr_connected.add_edges([(node.index, sink_id)])
                self.Gr_connected.es[self.Gr_connected.get_eid(node.index,sink_id)]['weight'] = weight_avg 
                self.Gr_connected.es[self.Gr_connected.get_eid(node.index,sink_id)]['pts'] = base.connector(sink_coord,node['o'])

    #Write skeleton connected to external node
        print(self.Gr_connected.is_connected(), ' connected')
        print('After connecting external nodes, G has vcount ', self.Gr_connected.vcount())
        connected_name = os.path.split(self.gsd_name)[0] + '/connected_' + os.path.split(self.gsd_name)[1] 
        #connected_name = self.stack_dir + '/connected_' + self.gsd_name 
        base.G_to_gsd(self.Gr_connected, connected_name)
        
        if R_j=='infinity': self.L = np.asarray(self.Gr.laplacian())
        else: self.weighted_Laplacian()
        F = np.zeros(sink_id+1)
        print(F.shape,'F')
        print(self.L.shape, 'L')
        F[source_id] = F_dim
        F[sink_id] = -F_dim
        np.save(self.stack_dir+'/L.npy',self.L)
        np.save(self.stack_dir+'/F.npy',F)
        P = np.matmul(np.linalg.pinv(self.L, hermitian=True),F)
        np.save(self.stack_dir+'/P.npy',P)

        self.P = P
        self.F = F

class StructuralNetwork(Network):
    """Child of generic SGT Network class.
    Equipped with methods for analysing structural networks
    """
    def __init__(self, directory):
        super().__init__(directory)
        
    def G_calc(self):
        avg_indices = dict()

        operations = [self.Gr.diameter, self.Gr.density, self.Gr.transitivity_undirected, self.Gr.assortativity_degree]
        names = ['Diameter', 'Density', 'Clustering', 'Assortativity by degree']

        for operation,name in zip(operations,names):
            start = time.time()
            avg_indices[name] = operation()
            end = time.time()
            print('Calculated ', name, ' in ', end-start)
            
        self.G_attributes = avg_indices
        
    def node_calc(self):
        self.Betweenness = self.Gr.betweenness()
        self.Closeness = self.Gr.closeness()
        self.Degree = self.Gr.degree()
