"""

This code is a modified version of the original `sknw.py` by Yan Xiaolong.

Modifications were made to address bugs caused by 'numba' on some platforms (e.g., Windows) and to replace fixed-size
NumPy buffers with dynamically resizable ones, improving robustness for large images and graphs.

Original author: Yan Xiaolong
Original source: https://github.com/Image-Py/sknw.git

"""


import numpy as np
# from numba import jit
import networkx as nx


def neighbors(shape):
    dim = len(shape)
    block = np.ones([3] * dim)
    block[tuple([1] * dim)] = 0
    idx = np.where(block > 0)
    idx = np.array(idx, dtype=np.uint8).T
    idx = np.array(idx - [1] * dim)
    acc = np.cumprod((1,) + shape[::-1][:-1])
    return np.dot(idx, acc[::-1])


# @jit(nopython=True)  # my mark
def mark(img, nbs):  # mark the array use (0, 1, 2)
    img = img.ravel()
    for p in range(len(img)):
        if img[p] == 0: continue
        s = 0
        for dp in nbs:
            if img[p + dp] != 0: s += 1
        if s == 2:
            img[p] = 1
        else:
            img[p] = 2


# @jit(nopython=True)  # trans index to r, c...
def idx2rc(idx, acc):
    rst = np.zeros((len(idx), len(acc)), dtype=np.int16)
    for i in range(len(idx)):
        for j in range(len(acc)):
            rst[i, j] = idx[i] // acc[j]
            idx[i] -= rst[i, j] * acc[j]
    rst -= 1
    return rst


# @jit(nopython=True)  # fill a node (maybe two or more points)
def fill(img, p, num, nbs, acc):
    cap = 131072
    buf = np.empty(cap, dtype=np.int64)
    img[p] = num
    buf[0] = p
    cur = 0
    s = 1
    iso = True

    while cur < s:
        p = buf[cur]
        for dp in nbs:
            cp = p + dp
            if img[cp] == 2:
                img[cp] = num
                if s >= cap:
                    cap *= 2
                    buf = np.resize(buf, cap)
                buf[s] = cp
                s += 1
            elif img[cp] == 1:
                iso = False
        cur += 1

    return iso, idx2rc(buf[:s], acc)


# @jit(nopython=True)  # trace the edge and use a buffer, then buf.copy if you use [] numba not works
def trace(img, p, nbs, acc):
    cap = 2048
    buf = np.empty(cap, dtype=np.int64)
    cur = 1
    c1 = 0
    c2 = 0
    newp = 0

    while True:
        if cur >= cap:
            cap *= 2
            buf = np.resize(buf, cap)
        buf[cur] = p
        img[p] = 0
        cur += 1

        for dp in nbs:
            cp = p + dp
            if img[cp] >= 10:
                if c1 == 0:
                    c1 = img[cp]
                    buf[0] = cp
                else:
                    c2 = img[cp]
                    if cur >= cap:
                        cap += 1
                        buf = np.resize(buf, cap)
                    buf[cur] = cp
            elif img[cp] == 1:
                newp = cp

        p = newp
        if c2 != 0:
            break

    return c1 - 10, c2 - 10, idx2rc(buf[:cur + 1], acc)


# @jit(nopython=True)  # parse the image, then get the nodes and edges
def parse_struc(img, nbs, acc, iso, ring):
    img = img.ravel()
    # buf = np.zeros(13107200, dtype=np.int64)
    num = 10
    nodes = []
    for p in range(len(img)):
        if img[p] == 2:
            isiso, nds = fill(img, p, num, nbs, acc)
            if isiso and not iso: continue
            num += 1
            nodes.append(nds)
    edges = []
    for p in range(len(img)):
        if img[p] < 10: continue
        for dp in nbs:
            if img[p + dp] == 1:
                edge = trace(img, p + dp, nbs, acc)
                edges.append(edge)
    if not ring: return nodes, edges
    for p in range(len(img)):
        if img[p] != 1: continue
        img[p] = num
        num += 1
        nodes.append(idx2rc([p], acc))
        for dp in nbs:
            if img[p + dp] == 1:
                edge = trace(img, p + dp, nbs, acc)
                edges.append(edge)
    return nodes, edges


# use nodes and edges to build a networkx graph
def build_graph(nodes, edges, multi=False, full=True):
    os = np.array([i.mean(axis=0) for i in nodes])
    if full: os = os.round().astype(np.uint16)
    graph = nx.MultiGraph() if multi else nx.Graph()
    for i in range(len(nodes)):
        graph.add_node(i, pts=nodes[i], o=os[i])
    for s, e, pts in edges:
        if full: pts[[0, -1]] = os[[s, e]]
        l = np.linalg.norm(pts[1:] - pts[:-1], axis=1).sum()
        graph.add_edge(s, e, pts=pts, weight=l)
    return graph


def mark_node(ske):
    buf = np.pad(ske, (1, 1), mode='constant').astype(np.uint16)
    nbs = neighbors(buf.shape)
    # acc = np.cumprod((1,) + buf.shape[::-1][:-1])[::-1]
    mark(buf, nbs)
    return buf


def build_sknw(ske, multi=False, iso=True, ring=True, full=True):
    buf = np.pad(ske, (1, 1), mode='constant').astype(np.uint16)
    nbs = neighbors(buf.shape)
    acc = np.cumprod((1,) + buf.shape[::-1][:-1])[::-1]
    mark(buf, nbs)
    nodes, edges = parse_struc(buf, nbs, acc, iso, ring)
    return build_graph(nodes, edges, multi, full)


# draw the graph
def draw_graph(img, graph, cn=255, ce=128):
    acc = np.cumprod((1,) + img.shape[::-1][:-1])[::-1]
    img = img.ravel()
    for (s, e) in graph.edges():
        eds = graph[s][e]
        if isinstance(graph, nx.MultiGraph):
            for i in eds:
                pts = eds[i]['pts']
                img[np.dot(pts, acc)] = ce
        else:
            img[np.dot(eds['pts'], acc)] = ce
    for idx in graph.nodes():
        pts = graph.nodes[idx]['pts']
        img[np.dot(pts, acc)] = cn
