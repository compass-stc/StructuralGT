import os
import numpy as np
from scipy.spatial.transform import Rotation as R

##### Removing duplicates #####
## Takes a 3D array where each element is a list of points that define a
## skeleton feature. Returns a truncated list of all the unique geometric
## representations of the given feature.
## Ensure np.shape(array) = (No features, 3, No of points in feature)
def unique(array):
    #First, removing duplicate lists
    x1=np.unique(array,axis=0)

    #Next, sort each list of points such that permutations become duplicates
    x2=[]
    for x in x1:
        indices = np.lexsort((x[0], x[1], x[2]))
        x2.append(x.T[indices])

    #Remove newly formed duplicates
    x2 = np.unique(x2,axis=0)

    #Retranspose
    xfin = []
    for x in x2:
        xfin.append(x.T)

    return np.asarray(xfin)

##### Rotation Matrix List #####
## To be applied to all base skelton feature arrays
## Q = (C,SX,SY,SZ)
##      where C = cos(theta/2)
##            S = sin(theta/2)
##            X,Y,Z = axis of rotation

theta = np.multiply([0,1,2,3,4,5,6,7],np.pi/4)
axes = ([1,0,0],[0,1,0],[0,0,1])
Q = lambda theta, ax: (np.cos(theta/2),ax[0]*np.sin(theta/2),ax[1]*np.sin(theta/2),ax[2]*np.sin(theta/2))

Rot_mat_list=[]
def permute(base):
    base=base.T
    x1=[]
    for axis1 in axes:
        for axis2 in axes:
            for axis3 in axes:
                for angle1 in theta:
                    for angle2 in theta:
                        for angle3 in theta:
                            Q1=Q(angle1, axis1)
                            Q2=Q(angle2, axis2)
                            Q3=Q(angle3, axis3)  #Compute quaternions


                            r1 = R.from_quat(Q1).as_matrix()
                            r2 = R.from_quat(Q2).as_matrix()
                            r3 = R.from_quat(Q3).as_matrix() #Convert to rotation matrices

                            # Apply 3 successive rotations to base list of points and append
                            # transformed points to list
                            x1.append(np.matmul(r3,np.matmul(r2,np.matmul(r1,base))))
    x1 = np.unique(x1,axis=0)
    x1 = np.where(x1 >= 0.01, 1, np.where(x1<=-0.01, -1,0)) #Round to either -1, 0 or 1

    x1 = unique(x1) + 1 # (shift the origin)

    return x1

##### Feature list #####
## Functions takes array from permute() and returns voxelised
## representation of the skeleton feature
def FList(CList):
    canvas = np.zeros((len(CList),3,3,3))
    for index,coords in enumerate(CList):
        canvas[index][CList[index][0],CList[index][1],CList[index][2]]=1

    return canvas

##### Write Permutation #####
## Parent function which writes unique permutations of a given skeleton feature to the current directory
def write_feature(base,name,dir_name):
    if os.path.isdir(dir_name)==False:
        os.mkdir(dir_name)

    features = FList(permute(base))
    np.save(dir_name  + '/' + name + '.npy',features)

