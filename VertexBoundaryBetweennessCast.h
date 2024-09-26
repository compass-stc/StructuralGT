#include <vector>

#ifndef VERTEXBOUNDARYBETWEENNESSCAST_H
#define VERTEXBOUNDARYBETWEENNESSCAST_H

namespace interface {
    class VertexBoundaryBetweennessCast {
        public:
            void* G_ptr;
            long long* sources_ptr;
            long long* targets_ptr;
            //std::vector<long long> sources;
            //std::vector<long long> targets;
            double* weights_ptr;
            int sources_len;
            int targets_len;
            VertexBoundaryBetweennessCast();
            ~VertexBoundaryBetweennessCast();
            void vertex_boundary_betweenness_compute();
            int num_vertices;
            int num_edges;
            std::vector<float> betweennesses;
    };
}

#endif
