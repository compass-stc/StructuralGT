import numpy as np
import igraph as ig

#For an unravelled image, this returns the relative indices for the neighbours of a given image shape.
#Eg if I have an image with shape (100,100), the neighbours of a particular image index, i, will be at i-101, i-100, ...
#This function returns that list
def neighbors(shape):
    dim = len(shape)
    block = np.ones([3]*dim)
    block[tuple([1]*dim)] = 0
    idx = np.where(block>0)
    idx = np.array(idx, dtype=np.uint8).T
    idx = np.array(idx-[1]*dim)
    acc = np.cumprod((1,)+shape[::-1][:-1])
    return np.dot(idx, acc[::-1])

#Examines non-zero voxels and marks them as
#  1 when voxel is edge
#  2 when voxel is node
def mark(img, nbs): # mark the array use (0, 1, 2)
    img = img.ravel()
    for p in range(len(img)):
        if img[p]==0:continue
        s = 0
        for dp in nbs:
            if img[p+dp]!=0:s+=1
        if s==2:img[p]=1
        else:img[p]=2

#idx is indices of neighbours of a node which are also nodes
#Function converts index locations in img to coordinates
def idx2rc(idx, acc):
    rst = np.zeros((len(idx), len(acc)), dtype=np.int16)
    for i in range(len(idx)):
        for j in range(len(acc)):
            rst[i,j] = idx[i]//acc[j]
            idx[i] -= rst[i,j]*acc[j]
    rst -= 1
    return rst
    

def fill(img, p, num, nbs, acc, buf):
    img[p] = num
    buf[0] = p
    cur = 0; s = 1; iso = True;
    
    while True:
        p = buf[cur]
        for dp in nbs: #for neighbour in neighbours of node
            cp = p+dp
            if img[cp]==2: #if neighbour of node is also node
                img[cp] = num #mark
                buf[s] = cp #store index of node position
                s+=1
            if img[cp]==1: iso=False #if node has an edge neighbour, it cannot be a one pixel node
        cur += 1
        if cur==s:break
    return iso, idx2rc(buf[:s], acc)

def trace(img, p, nbs, acc, buf):
    c1 = 0; c2 = 0;
    newp = 0
    cur = 1
    while True:
        buf[cur] = p
        img[p] = 0
        cur += 1
        for dp in nbs:
            cp = p + dp
            if img[cp] >= 10:
                if c1==0:
                    c1 = img[cp]
                    buf[0] = cp
                else:
                    c2 = img[cp]
                    buf[cur] = cp
            if img[cp] == 1:
                newp = cp
        p = newp
        if c2!=0:break

        #returns (node id1, node id2, pts)
    return (c1-10, c2-10, idx2rc(buf[:cur+1], acc))


def parse_struc(img, nbs, acc, iso, ring):
    img = img.ravel()
    buf = np.zeros(131072000, dtype=np.int64)
    #The image array is marked with num, where values of the same num correspond to voxels belonging to the same node
    num = 10
    nodes = []
    for p in range(len(img)):
        if img[p] == 2: #ie if voxel is node
            isiso, nds = fill(img, p, num, nbs, acc, buf)
            if isiso and not iso: continue
            num += 1
            nodes.append(nds)
    edges = []
    for p in range(len(img)):
        if img[p] <10: continue
        for dp in nbs:
            if img[p+dp]==1:
                edge = trace(img, p+dp, nbs, acc, buf)
                edges.append(edge)
    if not ring: return nodes, edges
    for p in range(len(img)):
        if img[p]!=1: continue
        img[p] = num; num += 1
        nodes.append(idx2rc([p], acc))
        for dp in nbs:
            if img[p+dp]==1:
                edge = trace(img, p+dp, nbs, acc, buf)
                edges.append(edge)
    return nodes, edges
    
# use nodes and edges build a networkx graph
def build_graph(nodes, edges, multi=False, full=True):
    #i is list of node positions where each item in list corresponds to a single node.
    #Each item may contain several points if the node spans several voxels
    #os is a list of centroids for each node
    #if full, os will be rounded to nearest voxel position
    os = np.array([i.mean(axis=0) for i in nodes])
    
    if full: os = os.round().astype(np.uint16)
    graph = ig.Graph()
    graph.add_vertices(len(nodes))
    graph.vs['pts'] = nodes
    graph.vs['o'] = os
    
    pts_list = []
    edge_list = []
    weight_list = []
    for s,e,pts in edges:
        edge_list.append((s,e))
        pts_list.append(pts)

    graph.add_edges(edge_list, attributes=dict(pts=pts_list)) 
    
    return graph

def mark_node(ske):
    buf = np.pad(ske, (1,1), mode='constant') #adds boundary to edges/faces of array
    nbs = neighbors(buf.shape) #buf.shape = ske.shape + (2,2,...)
    acc = np.cumprod((1,)+buf.shape[::-1][:-1])[::-1]
    mark(buf, nbs)
    return buf
def build_sknw(ske, multi=False, iso=True, ring=True, full=True):##
    buf = np.pad(ske, (1,1), mode='constant')###
    nbs = neighbors(buf.shape) #Relative indices of neighbors
    acc = np.cumprod((1,)+buf.shape[::-1][:-1])[::-1]
    mark(buf, nbs)
    nodes, edges = parse_struc(buf, nbs, acc, iso, ring)
    return build_graph(nodes, edges, multi, full)
    
# draw the graph
# Not yet igraph compatible
def draw_graph(img, graph, cn=255, ce=128):
    acc = np.cumprod((1,)+img.shape[::-1][:-1])[::-1]
    img = img.ravel()
    for (s, e) in graph.edges():
        eds = graph[s][e]
        if not graph.is_simple():
            for i in eds:
                pts = eds[i]['pts']
                img[np.dot(pts, acc)] = ce
        else: img[np.dot(eds['pts'], acc)] = ce
    for idx in graph.nodes():
        pts = graph.nodes[idx]['pts']
        img[np.dot(pts, acc)] = cn

if __name__ == '__main__':
    import matplotlib.pyplot as plt

    img = np.array([
        [0,0,0,1,0,0,0,0,0],
        [0,0,0,1,0,0,0,1,0],
        [0,0,0,1,0,0,0,0,0],
        [1,1,1,1,0,0,0,0,0],
        [0,0,0,0,1,0,0,0,0],
        [0,1,0,0,0,1,0,0,0],
        [1,0,1,0,0,1,1,1,1],
        [0,1,0,0,1,0,0,0,0],
        [0,0,0,1,0,0,0,0,0]])

    node_img = mark_node(img)
    graph = build_sknw(img, False, iso=True, ring=True)
    plt.imshow(node_img[1:-1,1:-1], cmap='gray')

    # draw edges by pts
    for (s,e) in graph.edges():
        ps = graph[s][e]['pts']
        plt.plot(ps[:,1], ps[:,0], 'green')
        
    # draw node by o
    nodes = graph.nodes()
    ps = np.array([nodes[i]['o'] for i in nodes])
    plt.plot(ps[:,1], ps[:,0], 'r.')

    # title and show
    plt.title('Build Graph')
    plt.show()
