#include <vector>

#ifndef BOUNDEDBETWEENNESSCAST_H
#define BOUNDEDBETWEENNESSCAST_H

namespace interface {
    class BoundedBetweennessCast {
        public:
            void* G_ptr;
            long* sources_ptr;
            long* targets_ptr;
            double* weights_ptr;
            int sources_len;
            int targets_len;
            BoundedBetweennessCast();
            ~BoundedBetweennessCast();
            void bounded_betweenness_compute();
            int num_edges;
            std::vector<float> betweennesses;
    };
}

#endif
