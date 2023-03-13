#include <vector>

#ifndef RANDOMBETWEENNESSCAST_H
#define RANDOMBETWEENNESSCAST_H

namespace interface {
    class RandomBetweennessCast {
        public:
            void* G_ptr;
            double* weights_ptr;
            std::vector<int> sources;
            std::vector<int> targets;
            int sources_len;
            int targets_len;
            RandomBetweennessCast();
            ~RandomBetweennessCast();
            void random_betweenness_compute();
            int num_edges;
            std::vector<float> betweennesses;
    };
}

#endif
