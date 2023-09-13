#include <vector>

#ifndef AVERAGENODALCONNECTIVITYCAST_H
#define AVERAGENODALCONNECTIVITYCAST_H
namespace interface {
    class AverageNodalConnectivityCast {
        public:
            void* G_ptr;
            AverageNodalConnectivityCast();
            ~AverageNodalConnectivityCast();
            void average_nodal_connectivity_compute();
            float anc;
    };
}

#endif
