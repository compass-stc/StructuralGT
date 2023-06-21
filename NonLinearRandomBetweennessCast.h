#include <vector>

#ifndef NONLINEARRANDOMBETWEENNESSCAST_H
#define NONLINEARRANDOMBETWEENNESSCAST_H

namespace interface {
    class NonLinearRandomBetweennessCast {
        public:
            void* G_ptr;
            double* weights_ptr;
            std::vector<int> sources;
            std::vector<int> targets;
            std::vector<float> incoming;
            int sources_len;
            int targets_len;
            NonLinearRandomBetweennessCast();
            ~NonLinearRandomBetweennessCast();
            void nonlinear_random_betweenness_compute();
            int num_edges;
            std::vector<float> betweennesses;
    };
}

#endif
