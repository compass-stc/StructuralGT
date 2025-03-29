# Copyright (c) 2023-2024 The Regents of the University of Michigan.
# This file is from the StructuralGT project, released under the BSD 3-Clause
# License.

# Much of this file is adapted from the bellybuttonseg repository at
# https://github.com/sdillavou/bellybuttonseg

import configparser
import copy
import gc
import os
from pathlib import Path

import cv2
import matplotlib.pyplot as plt
import numpy as np
import tensorflow as tf
from scipy.signal import convolve2d
from tensorflow.keras import Input, Model, layers
from tensorflow.keras.backend import clear_session
from tensorflow.keras.models import Sequential
from tensorflow.keras.optimizers import Adam
from tensorflow.keras.utils import to_categorical

from StructuralGT import base


class BBinputGenerator(tf.keras.utils.Sequence):

    def __init__(self, S_half=20, batch_size=32, flip=True, rotate=True, scales=1, scalefactor=2, randomize = True,**kwargs):
        super().__init__(**kwargs)

        self.S2 = S_half
        self.S = S_half*2+1
        self.batch_size = batch_size
        self.flip = flip
        self.rotate = rotate
        self.mult = 1*(1+3*rotate)*(1+flip) # flipping doubles, rotating 4x's unique images
        self.randomize = randomize
        self.getcount = 0
        self.maxgetcount = 100 # calls garbage collection every maxgetcount calls to __getitem__
        self.outstack = None
        self.scales = scales
        self.scalefactor = scalefactor
        self.padding = scalefactor**(scales-1)*S_half+1 # this is how far away the image edge must be from AOI
        self.input_shape = None # defined when first image is added

        # flag for changing mask to categorical, randomizing order, and adding weights.
        self.data_prepared = False
        # this is performed on the first call of __getitem__, and undone whenever new data is added (add_img or add_img_vec)

        if not int(batch_size/self.mult) == batch_size/self.mult:
            raise Exception('When manipulation (flipping/rotating) is on, batch size must be multiple of these manipulations.')

        self.dim3 = None # no images added yet!


        # Placeholder fields to be filled with add_image() method
        self.imgs = [] # first index is image number
        self.img_paddings = []


        # vectors to create output data (must always keep same order as each other)
        self.img_num = []
        self.rows = []
        self.cols = []
        self.label_list = [] # innie vs outie
        self.labels = None # this is in "categorical" terms, to be added by the first __getitem__ call

    # Add an image to the dataset (along with mask (innie/outie), AOI)
    # Uses add_img_vec after processing 2D data.
    def add_img(self,img, mask, AOI=None):

        img = np.copy(img)

        shp = np.shape(img)[:2]
        # reshape to 3D (with 3rd dimension 1), and record 2D shape
        #if len(np.shape(img)) == 2:
        assert len(np.shape(img)) == 2
        img = np.reshape(img,(shp[0],shp[1],1))

        # generate dummy mask and total AOI if needed
        if mask is None: # if not provided, we just need a space filler
            mask = np.ones(shp)
        if AOI is None: # if not provided, everything is in the area of interest
            AOI = np.ones(np.shape(mask))

        if (not shp == np.shape(mask)) or (not shp == np.shape(AOI)):
            raise Exception('img, mask, AOI, must have the same 2D shape')

        rowmat,colmat = np.mgrid[0:np.size(img,0),0:np.size(img,1)]

        # flatten AOI and check for multiple counts on a single pixel.
        # pixels will be repeated in the generator n = AOI[r,c] times
        AOI = np.ndarray.flatten(AOI)
        idx_used = []
        while np.max(AOI)>0:
            AOIbool = AOI>0
            AOI[AOIbool] -=1
            idx_used += list(np.argwhere(AOIbool))

        idx_used = np.ndarray.flatten(np.array(idx_used))

        # flatten all matrices, and use AOI to trim/duplicate indicees correctly
        rows = np.ndarray.flatten(rowmat)[idx_used]
        cols = np.ndarray.flatten(colmat)[idx_used]
        labels = np.ndarray.flatten(mask)[idx_used]

        # use method below to add the data to the generator!
        self.add_img_vec(img, rows, cols, labels)

        gc.collect()

    # Add an image to the dataset (along with rows, columns, and labels of points to generate data from)
    def add_img_vec(self,img, rows, cols, labels):

        if (not len(rows)==len(labels)) or (not len(cols) == len(labels)):
            raise Exception('rows, cols, and labels must have the same length L and be Lx1')

        shp = np.shape(img)
        if len(shp) == 2:
            self.imgs.append(np.copy(img).reshape(shp[0],shp[1],1))
            shp = np.array([shp[0],shp[1],1])
        else:
            self.imgs.append(np.copy(img))


        if self.dim3 is None:
            self.dim3 = shp[2]
            self.input_shape = self.S,self.S,self.scales*self.dim3

        elif not self.dim3 == shp[2]:
            raise Exception('Added images must have same 3rd dimension: '+str(self.dim3))

        #if weights is None:
        #    weights = np.ones(np.shape(rows)).astype(float)


        # determine how far away the AOI is from the edges of the image
        # (for rows and columns separately) then add padding to the image
        toppad = max(self.padding-np.min(rows),0)
        bottompad = max(self.padding-(shp[0]-np.max(rows)),0)
        leftpad = max(self.padding-np.min(cols),0)
        rightpad = max(self.padding-(shp[1]-np.max(cols)),0)
        padinstruction = ((toppad, bottompad), (leftpad, rightpad),(0,0)) # 3D

        self.imgs[-1] = np.pad(self.imgs[-1],padinstruction)
        self.img_paddings.append(padinstruction)

        rows = np.array(rows)+toppad # correct rows and columns  (labels are unchanged)
        cols = np.array(cols)+leftpad


        # add blurred version(s) of image to accomodate easy fetching of scaled up images
        # note that padding happens before blurring. However because blurred images are always subsampled
        # at the same frequency as the blur, this order does not effect the eventual outputs.
        baseimg = np.copy(self.imgs[-1])
        for scale in range(1,self.scales): # for every scale except 1 (powers of scalefactor)

            n = self.scalefactor**scale
            newimg = np.zeros(np.shape(baseimg))

            # blur at many scales and stack (concatenate) the images along the color axis
            for dim in range(self.dim3):
                newimg[:,:,dim] = convolve2d(baseimg[:,:,dim],np.ones((n,n))/(n**2), boundary='symm', mode='same')

            self.imgs[-1] = np.concatenate([self.imgs[-1],newimg],axis=2)


        self.rows = np.concatenate([self.rows,rows], axis=0).astype(int)
        self.cols = np.concatenate([self.cols,cols], axis=0).astype(int)
        self.img_num = np.concatenate([self.img_num,[len(self.imgs)-1 for _ in rows]], axis=0).astype(int)
        self.label_list = np.concatenate([self.label_list, labels], axis=0).astype(int)

        self.data_prepared = False # adding more images makes the entire data set no longer prepped!

    # returns a 2D map of innie vs outie mask (with any added padding removed)
    def get_masks(self,idx=0):
        out = np.zeros(np.shape(self.imgs[idx])[:2]) # same 2D shape as image, no channels.
        want = self.img_num == idx
        out[self.rows[want],self.cols[want]] = self.label_list[want]
        p = self.get_padding_array(idx)
        return out[p[0]:p[1],p[2]:p[3]]

    # returns a 2D map of Area of Interest (AOI) for image idx (with any added padding removed)
    def get_AOI(self,idx=0):
        out = np.zeros(np.shape(self.imgs[idx])[:2]) # same 2D shape as image, no channels.
        want = self.img_num == idx
        out[self.rows[want],self.cols[want]] = 1
        p = self.get_padding_array(idx)
        return out[p[0]:p[1],p[2]:p[3]]

    # returns an input image with any added padding removed
    def get_img(self,idx=0):
        p = self.get_padding_array(idx)
        return self.imgs[idx][p[0]:p[1],p[2]:p[3],:self.dim3] # cut out scalings

    # returns array with indicees required to remove padding from an image
    def get_padding_array(self,idx):
        p = np.ndarray.flatten(np.array(self.img_paddings[idx]))
        p[1] = np.shape(self.imgs[idx])[0]-p[1]
        p[3] = np.shape(self.imgs[idx])[1]-p[3]
        return p

    # normalize all images in this generator -- sends maxval to 0.5 and minval to -0.5
    def normalize_images(self):
        maxval,minval = np.max(self.get_img(0)),np.min(self.get_img(0))
        for idx in range(1,len(self.imgs)):
            maxval = np.max([maxval,np.max(self.get_img(idx))])
            minval = np.min([minval,np.min(self.get_img(idx))])

        self.maxval = maxval
        self.minval = minval

        #for idx in range(np.shape(self.imgs)[0]):
        for idx in range(len(self.imgs)):
            self.imgs[idx] = (self.imgs[idx]-self.minval)/(self.maxval-self.minval) - 0.5

    # returns an array of 2D predictions for each image in self.imgs, based on the model given.
    def get_prediction(self,model):

        #Models with these features will generate multiple predictions per pixel and will not match with the
        # internal arrays like self.rows/self.cols. It will be massively inefficient and is thus prevented.
        if self.rotate or self.flip:
            raise Exception('This generator has flips or rotates and should not be used as a prediction generator.')

        # do the prediction!
        outputs = model.predict(self)
        class_vec = outputs[:,1]


        predictions = []
        #for idx in range(np.shape(self.imgs)[0]): # for every image, find predictions
        for idx in range(len(self.imgs)): # for every image, find predictions
            want = self.img_num == idx # identify which elements are for this image
            dummy_img = np.zeros(np.shape(self.imgs[idx])[:2])
            dummy_img[self.rows[want],self.cols[want]] = class_vec[want] # place predictions in 2D

            # remove padding
            p = np.ndarray.flatten(np.array(self.img_paddings[idx]))
            p[1] = np.shape(self.imgs[idx])[0]-p[1]
            p[3] = np.shape(self.imgs[idx])[1]-p[3]

            # add to overall output array
            predictions.append(dummy_img[p[0]:p[1],p[2]:p[3]])

        return predictions

    def shuffle(self):

        ordr = np.arange(len(self.rows))
        np.random.shuffle(ordr)

        self.label_list = self.label_list[ordr]
        self.rows = self.rows[ordr]
        self.cols = self.cols[ordr]
        self.img_num = self.img_num[ordr]


    # return the number of batches to pull for an epoch of training
    def __len__(self):
        return np.ceil(self.mult*len(self.label_list)/self.batch_size).astype(int)

    # return a batch of data. This may include rotations and flips, as well as multiple channels and/or scales
    def __getitem__(self, idx00):

        self.getcount += 1
        if self.getcount >= self.maxgetcount:
            gc.collect()
            self.getcount=0

        if not self.data_prepared: # happens only on the first call.

            self.label_list = self.label_list>0        # create binary categorization

            if self.randomize: # if randomization is in the cards, deal.
                self.shuffle()

            self.labels = to_categorical(self.label_list) # make Keras-friendly labels

            self.data_prepared = True # data is now prepped.


        # identify what the unique index and number of unique elements in the batch is (repeats are flips/rots)
        idx0 = idx00/self.mult
        batch = self.batch_size/self.mult

        # Indices of the data to be pulled.
        # Repeat self.mult times and sort to give an ordered list [32,32,...,32,83,83...,83,120,...]
        vec = sorted(np.repeat(np.arange((idx0*batch),np.min([(idx0+1)*batch,len(self.labels)]),dtype='int'),self.mult))

        # Scales to pull. If self.scales=1, this will just be 1.
        scalevec = np.power(self.scalefactor,np.arange(self.scales)) # e.g. 1,2,4,8, etc

        # create stacked image output.
        # Images may have multiple channels (e.g. colors) and scales: these are stacked in the same dimension (3 in this stack).
        # There will also be self.mult repeats of every such color and scale stack (for later rotation/flipping).
        # Output stack dimensions are [self.batch_size,self.S,self.S,self.dim3*self.scales] with [batch] unique elements.

        self.outstack = np.stack([ \
            np.concatenate([ \
                self.imgs[self.img_num[idx]][self.rows[idx]-self.S2*s:self.rows[idx]+self.S2*s+1:s, \
                             self.cols[idx]-self.S2*s:self.cols[idx]+self.S2*s+1:s, \
                             self.dim3*snum:self.dim3*(snum+1)].reshape(self.S,self.S,self.dim3) \
                for s,snum in zip(scalevec,range(self.scales))], axis=2) for idx in vec] ,axis=0)

        # If rotations/flips are used, go through stack and modify unaltered images to create these new data.
        if self.flip or self.rotate:
            multiscaledim3= self.scales*self.dim3

            # rotate and flip depending on idx (which indicates which repeat # of a given environment this is)
            for idx in range(len(vec)):
                # reshape image so that it can use numpy rotation/flip functions
                snap = self.outstack[idx,:,:,:].reshape(self.S,self.S,multiscaledim3)

                # rotate 90 degrees for every additional index (stack is sorted by index, so this achieves desired effect)
                if self.rotate:
                    snap = np.rot90(snap,idx%4)

                # flip half of the images if self.flip
                if self.flip and (idx%self.mult)>=self.mult/2:
                    snap = np.fliplr(snap)

                # reshape to put back into stack
                self.outstack[idx,:,:,:] = snap.reshape([1,self.S,self.S,multiscaledim3])

        return  np.copy(self.outstack), np.array(self.labels[vec])


def fractionalize_AOI(masks, AOIs, fraction,balance_classes):

    train_innie,train_total = 0,0

    for k,AOI_dummy in enumerate(AOIs):
        train_innie += np.sum((masks[k]>0)*AOI_dummy)
        train_total += np.sum(AOI_dummy)

    train_outie = train_total-train_innie

    datapoints_unbalanced = np.array([train_outie,train_innie])*fraction
    datapoints_balanced = np.array([1,1])*np.mean(datapoints_unbalanced)

    datapoints_final = balance_classes*datapoints_balanced + (1-balance_classes)*datapoints_unbalanced

    train_frac = datapoints_final/datapoints_unbalanced*fraction

    print('[BB] Balancing innies vs outies ',np.round(balance_classes*100,2),'% (0% = random sampling, 100% = balanced)')
    print('[BB] Result is innies x',np.round(train_frac[1],2),'~',int(datapoints_final[1]),' datapoints, outies x',np.round(train_frac[0],2),'~',int(datapoints_final[0]),' datapoints.')


    for k in range(len(AOIs)):

        train_delta2 = train_frac-1 # fraction above or below using all data
        checkmask = masks[k] > 0
        AOImask = 0*AOIs[k] + 1

        for inout in [0,1]:

            while train_delta2[inout] >=1: # if small enough, one class may need to be added multiple times
                train_delta2[inout] -=1
                AOImask[checkmask==inout]+=1

            # adjust by remaining delta, so that innies are now fraction/2 of AOI (may be counted 2 or more times per px)
            dummy = np.random.choice([0, 1], size=AOImask.shape, p=(1-abs(train_delta2[inout]), abs(train_delta2[inout])))
            # add to AOI count if positive adjustment, subtract from it if negative (np.sign)

            AOImask[checkmask==inout] += (np.sign(train_delta2[inout])*dummy[checkmask==inout]).astype(int)

        AOIs[k]  = AOImask*AOIs[k]

    return AOIs

def save_parameters(filename,keys,vals):

    config = configparser.RawConfigParser()

    config.add_section('Parameters')

    for k,v in zip(keys,vals):
        config.set('Parameters',  k.lower(), v)

    with open(filename+'.txt', 'w') as configfile:
          config.write(configfile)

# Load parameters from a filename. Any missing values from param_types will be filled with default values.
def load_parameters(filename,param_types):
    assert os.path.exists(filename+'.txt')
    config = configparser.ConfigParser()
    config.read(filename+'.txt')

    keys = list(param_types.keys())
    values = list(param_types.values())

    out = [None for _ in keys]
    keys2 = [k.lower() for k in keys]

    # load value from file
    for key in config['Parameters']:
        if key.lower() in keys2:
            out[keys2.index(key.lower())]=config['Parameters'][key.lower()]

    param = LoadConverter(out,values)
    param = dict(zip(keys,param))

    # add default values if not included
    param2 = create_default_params()


    for k in param2.keys():
        if (k in param) and param[k] is None:
            param[k] = param2[k]

    return param



#Convert array of parameters formatted as strings into array of parameters formatted according to param_var_types
def LoadConverter(param_array,param_var_types):
    for ind in range(len(param_array)):
        if not param_array[ind] is None:
            param_array[ind] = param_var_types[ind](param_array[ind])
    return param_array


def load_image(filepath, binarize = False, integerize = False, RGB_to_gray = False):

    if filepath is None:
        return None

    if filepath[-4:] == '.txt': # load text
        img = np.array(np.loadtxt(filepath,skiprows=0))
    else: # load image file
        img = cv2.imread(filepath, cv2.IMREAD_ANYDEPTH)
        if img is None:
            print('Default image loading method failed, trying backup')
            img = cv2.imread(filepath)
        if img is None:
            raise Exception('Loaded image is empty')
        if len(np.unique(img)) == 1:
            print('Only one value for the entire image '+filepath)


    # average color channels
    if RGB_to_gray:
        print('Converting '+ filepath + ' to grayscale before use.')
        if len(np.shape(img))==3 and np.shape(img)[2]==3:
            img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        elif len(np.shape(img))>=3:
            print('Error for: '+filepath)
            raise Exception('Attempted to convert to grayscale but image has more than 3 color channels or a 4th dimension')

    # convert all non-zero values to 1's
    if binarize:
        if len(np.shape(img))>2 and np.shape(img)[2]>1:
            for k in range(1,np.shape(img)[2]):
                if not np.array_equal(img[:,:,0], img[:,:,k]):
                    raise Exception('Attempting to binarize image with multiple and different color channels.')
            img = img[:,:,0] # reduce to one channel

        img = 1*(img!=0)

    # convert unique values into unique integers. 0 is interpreted as background (outies)
    if integerize: # segmenting already does this
        S = np.shape(img)
        if len(S)>2 and S[2]>1:
            for k in range(1,S[2]):
                if not np.array_equal(img[:,:,0], img[:,:,k]):
                    raise Exception('Attempting to integerize image with multiple and different color channels.')
            img = np.sum(img,tuple(k for k in range(2,len(S)))) # reduce to one channel

         # take unique values and convert them to indicees
        U = np.unique(img)
        img2 = np.copy(img)
        for idx,val in enumerate(U):
            img[img2==val] = idx+1

        img[img2==0] = 0 # maintain background as background (it was assigned a different value above)
        img = np.array(img,dtype=int)
    return img


# find masks from filenames mask_names with matching names (ignore file extension and letter case) to the image filenames in img_names
# return a list of mask names that match, in the same order as img_names
# if use_default is selected and a mask (aoi) is present with the base name "default", then it will be used when no match is found
def find_matching_masks(img_names, mask_names, raise_issues=True,use_default=False):

    img_name_bases = [name[:name.index('.')].lower() for name in img_names]
    mask_name_bases = [name[:name.index('.')].lower() for name in mask_names]

    defaultstr = 'default'

    if use_default and (defaultstr in mask_name_bases): # use the mask/aoi specified as default when none is found
        defaultidx = mask_name_bases.index(defaultstr)
    else:
        defaultidx = None

    mask_idxs = [mask_name_bases.index(img_name) if img_name in mask_name_bases else defaultidx for img_name in img_name_bases]

    if raise_issues and None in mask_idxs:
        raise Exception('Masks are missing for the following images: '+', '.join([name for name, idx in zip(img_names,mask_idxs) if idx is None]))


    return [mask_names[k] if not k is None else None for k in mask_idxs]


# returns a string listing input image names and their sizes
def list_imgs_and_sizes(img_names,imgs):
    # str call makes None type into 'None'
    out = [str(name) + ' ('+','.join(str(k) for k in np.shape(img))+')' for name,img in zip(img_names,imgs)]
    return ', '.join(out)

# returns a list of filenames (assumption is they are all images or text)
# want is indicees of desired images (None -> all files), count is total number of names returned (always a subset of want/all)
def get_image_list(folder, want = None, count=-1):

    assert os.path.exists(folder)
    names = []
    for _file in os.listdir(folder):
        if base.Q_img(_file):
            names.append(_file)

    # want = set of images to draw from (None means all). count = number of images to end up with (-1 means all)
    if count ==-1: # take all images of want
        if want is None:
            want = np.linspace(0, len(names)-1,len(names))

    elif count >= 0: # take [count] images
        if want is None:
            want = np.linspace(0, len(names)-1, count)
        else:
            want = want[np.linspace(0, len(want)-1, count)]

    else: # count needs to be positive or -1
        raise Exception('Image counting parameter has an illegal value.')

    # narrow names down only to desired ones, then create array for images
    return [names[int(k)] for k in want]



# returns images of a list of filenames for a given folder
def load_image_list(folder, names, binarize = False, integerize = False, RGB_to_gray = False, chatter = True):

    if RGB_to_gray and (not integerize) and (not binarize) and chatter:
        index = folder.rfind('/') # include only this folder's name (not filepath)

    names2 = copy.copy(names)
    for i,name in enumerate(names2):
        if not name is None:
            names2[i] = folder + '/' + name

    return [load_image(name, binarize = binarize, \
                          integerize = integerize, RGB_to_gray = RGB_to_gray) \
                          for name in names2]



# create parameter dict without rarely-edited values
def create_default_params():

    param = {};

    param['s_half'] = 12# int, defines size of input image to NN: size = (2[S_half]+1 square). 12 is reccommended.

    param['scales'] = 4 # number of scaled images (int, 1 is just regular without scaling)
    param['scalefactor'] = 2 # scale multiplier (int)
    # for example, with 3 scales of scalefactor 4, images scaled by 1, 4^1=4, and 4^2=16 are included as inputs

    param['batch_size'] = 1024 # int, must be multiple of 8 to allow rotations + flips. Same size for testing.
    #True/False
    param['rotations'] = 1 # rotate images by 90, 180, 270 degrees in training to multiply data by 4
    param['flips'] = 1 # flip images in training to multiply data by 2

    #True/False
    param['images_to_grayscale'] = 1; #convert images to grayscale (if images already one channel, this has no effect.)

    param['train_epochs'] = 3; # how many epochs to train

    # (total AOI area)*fraction = training samples
    # These are automatically adjusted such that half come from each class, meaning some may be multi-counted.
    # This does not affect test set.
    param['fraction'] = 0.3

    # 1: balances the number of innies and outies in the training set. 0: no balancing. fraction: interpolates between the two.
    param['balance_classes'] = 1

    param['track_outies']  = 0 # invert inputs and track 'outies' instead (works for small, separated particles)

    # Specify the type(s) of final images to be saved, True(1) or False(0)
    param['output_binarized']=0

    return param

def model_S_half_minimum(model_num):

    if model_num == 1:
        return 9
    else:
        raise Exception('Model Number Not Recognized.')


# Create a keras sequential NN that will train using the input train_gen (training data generator).
def generate_network(input_shape):

    clear_session()

    #create model
    model = Sequential()



    inputs = Input(shape=input_shape, name="img")
    x = layers.Conv2D(64, 3, activation="relu")(inputs)
    x = layers.Conv2D(32, 3, activation="relu")(x)
    block_1_output = layers.MaxPooling2D(pool_size=(2,2))(x)

    x = layers.Conv2D(32, 3, activation="relu", padding="same")(block_1_output)
    x = layers.Dropout(.1)(x)
    x = layers.Conv2D(32, 3, activation="relu", padding="same")(x)
    block_2_output = layers.add([x, block_1_output])
    block_2_output = layers.MaxPooling2D(pool_size=(2,2))(block_2_output)

    x = layers.Conv2D(32, 3, activation="relu", padding="same")(block_2_output)
    x = layers.Dropout(.1)(x)
    x = layers.Conv2D(32, 3, activation="relu", padding="same")(x)
    block_3_output = layers.add([x, block_2_output])
    block_3_output = layers.MaxPooling2D(pool_size=(2,2))(block_3_output)

    x = layers.Flatten()(block_3_output)
    x = layers.Dense(64, activation="relu")(x)
    x = layers.Dropout(.1)(x)
    x = layers.Dense(64, activation="relu")(x)
    x = layers.Dropout(.1)(x)
    x = layers.Dense(64, activation="relu")(x)
    x = layers.Dropout(.1)(x)
    x = layers.Dense(64, activation="relu")(x)
    x = layers.Dropout(.1)(x)

    outputs = layers.Dense(2,activation="softmax",name="category_output")(x)


    model = Model(inputs, [outputs,], name="BB_resnet_2out")

    losses = {
    "category_output": "categorical_crossentropy",
    }
    lossWeights = {"category_output": 1.0,}

    opt = Adam(learning_rate = 0.001)

    model.compile(optimizer=opt, loss=losses, loss_weights=lossWeights, metrics=['accuracy'])

    return model


def CreateGenerator(img_path, root, param, want=None, count=-1, train_test_predict=0, index = -1, chatter = False):

    # determine type of generator
    if train_test_predict == 0: # training generator: include manipulations of data and shuffle data
        flip,rotate,randomize = param['flips'],param['rotations'],True
    elif train_test_predict == 1 or train_test_predict == 2: # testing/prediction generator: leave data alone
        flip,rotate,randomize = False,False,False
    else:
        raise Exception('train_test_predict parameter must be 0 (training), 1 (testing), or 2 (predicting).')


    dataGenerator = BBinputGenerator(S_half = param['s_half'], \
                                      batch_size = param['batch_size'],\
                                      scales=param['scales'], \
                                      scalefactor=param['scalefactor'], \
                                      flip=flip, rotate=rotate, randomize=randomize,)

    # load images specified in inputs
    img_names = get_image_list(img_path, want=want, count=count)

    if train_test_predict == 0 and len(img_names)==0:
        raise Exception('Attempt to create training generator without any images!')

    if index!=-1:
        if index>=len(img_names):
            raise IndexError('Index outside of want list')
        else:
            img_names = [img_names[index]]
    imgs = load_image_list(img_path, img_names, RGB_to_gray=param['images_to_grayscale'], chatter = chatter)
    if chatter:
        print('[BB] -- '+img_path+' images: '+list_imgs_and_sizes(img_names,imgs))

    # if training or testing, we need masks, find names
    if train_test_predict < 2:
        mask_folder = root+'/masks' #!!!!!!!!!!!!!!!!!!
        assert os.path.exists(mask_folder)
        mask_names = find_matching_masks(img_names, get_image_list(mask_folder))
        masks = load_image_list(mask_folder,mask_names, integerize=True,RGB_to_gray = True)
        if chatter:
            print('[BB] -- '+root+' masks: '+list_imgs_and_sizes(mask_names,masks))
    else:
        masks = [None for k in imgs]

    # look for AOIs, load them (allow only 1's and 0's)
    AOI_folder = root+'/areas_of_interest' #!!!!!!!!!!!!!!!!!!
    if not os.path.exists(AOI_folder):
        os.mkdir(AOI_folder)

    AOI_names = find_matching_masks(img_names, get_image_list(AOI_folder), raise_issues=False,use_default=True)
    AOIs = load_image_list(AOI_folder, AOI_names, binarize=True)

    # for all non-defined AOIs, assume entire image is fair game
    for k,img in enumerate(imgs):
        if AOIs[k] is None:
            AOIs[k] = np.ones(np.shape(img))

    if chatter:
        print('[BB] -- '+root+' AOIs: '+list_imgs_and_sizes(AOI_names,AOIs))

    # Enforce specified fraction of data if training set
    if train_test_predict == 0:
        AOIs = fractionalize_AOI(masks, AOIs, param['fraction'],param['balance_classes'])


    # if there are masks and track_outies flag is true, alert user and invert masks
    if param['track_outies'] and np.sum([not m is None for m in masks])>0:
        if chatter:
            print('[BB] -- Inverting masks to track zero-valued pixels.')
        masks = [1*(m == 0) if (not m is None) else None for m in masks]

    # create HP inputs
    for k,img in enumerate(imgs):
        #dataGenerator.add_ID_img(img, mask=masks[k], AOI=AOIs[k], neighborhood_radius=param['border_radius'], particle_border_mult=param['particle_border_weighting'], two_particle_mult=param['two_particle_border_weighting'],  img_edge_mult = param['image_border_weighting'])
        dataGenerator.add_img(img, mask=masks[k], AOI=AOIs[k])#, neighborhood_radius=param['border_radius'])

    dataGenerator.normalize_images()

    return dataGenerator, img_names

#Dictionary key for text and variable translation for image_dict, used in SegmentPrediction, UpdateAccTable, SaveImage and SaveMatrix functions
possible_prediction_names = {'output_binarized':'outmask','output_classprob':'mask'}

def convert_param_to_outputs(param):
    to_save = []
    #Iterate through param variables
    for key in param:
        #Find the variables related to output formatting
        if key in possible_prediction_names.keys():
            #Select only the desired formats for output
            if param[key]:
                #remove the 'output' tag from the string and add to final list
                to_save.append(key[6:])
    return to_save

#Save segmented matrix as image
#COME BACK AND CLEAN UP THIS KEY THING ITS STUPID
def SaveImage(BB_output_folder,name,image_dict,images_to_save):
    pixel_scaling = {'_binarized': 250,'_classprob': 250,'_segmented': 97,'_markers': 97}
    for key in images_to_save:
        dummymat = np.array((pixel_scaling[key]*image_dict[key]) % 251,dtype=int)
        cv2.imwrite(BB_output_folder+'/'+name[:name.index('.')]+key+'.png',np.array((image_dict[key]>0)*4+dummymat, dtype=np.uint8))

#Load model parameters from a filepath, institute a model, load weights from a checkpoint (if any) and perform any
#additional training required using the train_gen and test_gen. Save new information to new output path? Add number of
#epochs already completed as a stored value in a filename?
def CreateModel(param,outputfilename,train_gen=None,test_gen=None,chkpt_filepath = None):

    #Create model
    S = param['s_half']*2+1
    img_shapes = [S,S,param['scales']*param['dim3']]
    modelBB = generate_network(img_shapes)

    BB_weight_filename = outputfilename+'/networkweights.weights.h5'


    if chkpt_filepath is not None:
        print('[BB] Loading model weights from previous checkpoint')
        modelBB.load_weights(chkpt_filepath)


    #Train the model more if desired
    if param['train_epochs']!=0:
        if train_gen is None:
            raise Exception('[DEBUG] THERE IS NO GENERATOR OF TRAINING DATA TO TRAIN ON')

        # Create a callback that saves the model's weights every epoch
        cp_callback = tf.keras.callbacks.ModelCheckpoint(filepath=BB_weight_filename, verbose=1, save_weights_only=True)

        modelBB.fit(train_gen, validation_data=test_gen, epochs=param['train_epochs'],callbacks=[cp_callback]);

    return modelBB

# Predict function that takes in a generator and model, returns a prediction
# This function has been modified so that it no longer returns accuracies; that should be done in a separate function
def Predict(param, model, gen, BB_output_folder, names):
    '''
    inputs:
    param: list of parameters
        including save_to_png and save_to_npy which specify file type to save
        and outputs to save: '_segmented', '_binarized', '_dist', '_classprob', '_markers' (seeds for watershedding)
    model: trained model used for prediction
    gen: generator of images for prediction
    BB_output_folder: filepath for saving segmented predictions
    names: list of original image names for saving predictions
    '''

    BBpredictions = gen.get_prediction(model)
    images_to_save = convert_param_to_outputs(param)

    image_dict = {}
    for k, BBout in enumerate(BBpredictions):
        image_dict['_binarized'] = BBout>0.5
        SaveImage(BB_output_folder,names[k],image_dict,images_to_save)

class deeplearner:
    def __init__(self, root, params='base_parameters', model_dir='model', train_img_count=-1, test_img_count=-1, want_train=None, want_test=None):
        """_summary_

        Args:
            root (str): High level path to the data. This directory must exist.
            model_dir (str): Directory to store/use the model. This directory will be created if it does not exist.
            params (str or dict): Model params
            train_img_count (int, optional): _description_. Defaults to -1.
            test_img_count (int, optional): _description_. Defaults to -1.
        """
        self.root = root
        self.model_dir = model_dir
        self.want_train = want_train
        self.want_test = want_test
        if isinstance(params, dict):
            self.params = params
        elif isinstance(params, str):
            self.params = load_parameters(self.root + '/' + params, param_types)

        # Training batch size must be correct multiple when using rotations/flips
        unique_in_batch = self.params['batch_size']/((1+3*self.params['rotations'])*(1+self.params['flips']))
        if not unique_in_batch == int(unique_in_batch):
            raise Exception('Batch number must be divisible by 4 if doing rotations, 2 if flipping, and 8 if both.')

        # input window size must be big enough for selected network
        if not self.params['s_half'] >= 9:
            raise Exception('Input window size must be at least 9 pixels in radius.')

        self.train_img_count = train_img_count
        self.test_img_count = test_img_count

        if not os.path.exists(self.model_dir):
            os.mkdir(self.model_dir)

        self.output_dir = self.root + '/' + model_dir
        self.parameter_filename = self.output_dir+'/parameters'
        self.HP_weight_filename = self.output_dir+'/networkweights.weights.h5'
        self.normalization_filename = self.output_dir+'/normalization'

        S = self.params['s_half']*2+1
        img_shapes = [S,S,self.params['scales']*self.params['dim3']]
        self.modelHP = generate_network(img_shapes)

    def train(self, override_param=None):
        #Adjust loaded (old) parameters to match any input (new) parameters
        if override_param is not None:
            for key,value in override_param.items():
                self.params[key] = param_types[key](value)

        train_genHP,_ = CreateGenerator(self.root + '/train_images', self.root,\
                                    param=self.params, want=self.want_train, \
                                    count=self.train_img_count,
                                    train_test_predict=0)

        if include_test_in_training:
            test_genHP,_ = CreateGenerator(self.root + '/test_images', self.root,\
                                        param=self.params, want=self.want_test, \
                                        count=self.test_img_count,
                                        train_test_predict=1)
        else:
            test_genHP = None

        print('[BB] Training Neural Network')
        if not include_test_in_training:
            print('[BB] -- Excluding test images from .fit function. Test set results available at end.')

        # save parameters
        save_parameters(self.parameter_filename,list(self.params.keys()),list(self.params.values()))
        save_parameters(self.normalization_filename,['img_max', 'img_min'],[train_genHP.maxval, train_genHP.minval])

        cp_callback = tf.keras.callbacks.ModelCheckpoint(filepath=self.HP_weight_filename, verbose=1, save_weights_only=True)

        self.modelHP.fit(train_genHP, validation_data=test_genHP, epochs=self.params['train_epochs'],callbacks=[cp_callback])

        # garbage collect
        del train_genHP
        del test_genHP
        gc.collect()

    def load_weights(self, chkpt_filepath=None):
        if chkpt_filepath is None:
            chkpt_filepath = self.HP_weight_filename
        self.modelHP.load_weights(chkpt_filepath)


    def predict(self, network, predict_path=None):

        HP_output_folder = network.stack_dir

        if predict_path is None:
            predict_path = network.dir

        more_data = True
        index = 0
        while more_data:
            try:
                all_genHP,img_names= CreateGenerator(network.dir, self.root, param=self.params, train_test_predict=2, index = index)

                #Predict(self.params, self.modelHP, all_genHP, HP_output_folder, img_names)
                BBpredictions = all_genHP.get_prediction(self.modelHP)

                    #images_to_save = convert_param_to_outputs(param)

                    #image_dict = {}
                for k, BBout in enumerate(BBpredictions):
                    self.BBout = BBout
                    _binarized = np.array(BBout>0.5)
                    cv2.imwrite(network.stack_dir+'/slice0000.tiff',np.array(BBout>0.5, dtype=np.uint8)*255)
                    #SaveImage(BB_output_folder,names[k],image_dict,images_to_save)


                print('[BB] -- Generated Prediction Image Result '+str(index)+': '+img_names[0])

                index+=1
                #del all_genHP
                gc.collect()
            except IndexError:
                more_data= False
