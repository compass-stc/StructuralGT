#include <vector>

#ifndef RANDOMBOUNDARYBETWEENNESSCAST_H
#define RANDOMBOUNDARYBETWEENNESSCAST_H

namespace interface {
    class RandomBoundaryBetweennessCast {
        public:
            void* G_ptr;
            double* weights_ptr;
            std::vector<int> sources;
            std::vector<int> targets;
            std::vector<float> incoming;
            int sources_len;
            int targets_len;
            RandomBoundaryBetweennessCast();
            ~RandomBoundaryBetweennessCast();
            void random_boundary_betweenness_compute();
            int num_edges;
            std::vector<float> linear_betweennesses;
            std::vector<float> nonlinear_betweennesses;
    };
}

#endif
