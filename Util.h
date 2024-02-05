#include <igraph.h>
#include <vector>
#include <Eigen/Dense>

//Casts an igraph vector to a std::vector. The assignemnet operator may not 
//be overloaded for a class that had been defined elsewhere. Hence I am using 
//<<= instead.
std::vector<float>& operator<<=(std::vector<float>& V, igraph_vector_t& I) {
    for (int i=0; i<igraph_vector_size(&I); i++) {
        V.push_back(VECTOR(I)[i]);
    }
    return V;
}

//Casts a square igraph matrix to a vector of std::vectors. 
std::vector<std::vector<float> >& operator<<=(std::vector<std::vector<float> >& V, igraph_matrix_t& I) {
    std::vector<float> _V(igraph_matrix_nrow(&I));
    for (int i=0; i<igraph_matrix_nrow(&I); i++) {
        for (int j=0; j<igraph_matrix_nrow(&I); j++) {
            _V[j] = MATRIX(I,i,j);
        }
        V.push_back(_V);
    }
    return V;
}

std::vector<float>& operator<<=(std::vector<float>& V, Eigen::VectorXf& E){
    for (int i=0; i<E.size(); i++) {
        V.push_back(E[i]);
    }
    return V;
}
