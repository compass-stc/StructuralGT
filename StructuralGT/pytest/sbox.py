import igraph

G1 = igraph.Graph.K_Regular(10, 2)
G2 = igraph.Graph.K_Regular(10, 2)

def graph_function(G):
    print(G.degree())

graph_function(list(G1,G2))


