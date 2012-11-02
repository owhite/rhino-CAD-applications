#include "LK.h"

/*
   The Minimum1TreeCost function returns the cost of a minimum 1-tree.

   The minimum 1-tre is found by determining the minimum spanning tree and 
   then adding an edge corresponding to the second nearest neighbor of one 
   of the leaves of the tree (any node which has degree 1). The leaf chosen
   is the one that has the longest second nearest neighbor distance.

   The V-value of a node is its degree minus 2. Therefore, Norm being the 
   sum of squares of all V-values, is a measure of a minimum 1-tree/s 
   discrepancy from a tour. If Norm is zero, then the 1-tree constitutes a 
   tour, and an optimal tour has been found.
*/

double Minimum1TreeCost(const int Sparse)
{
    Node *N, *N1;
    double Sum = 0;
    long Max;

    MinimumSpanningTree(Sparse);
    N = FirstNode;
    do {
        N->V = -2;
        Sum += N->Pi;
    }
    while ((N = N->Suc) != FirstNode);
    Sum *= -2;
    while ((N = N->Suc) != FirstNode) {
        N->V++;
        N->Dad->V++;
        Sum += N->Cost;
        N->Next = 0;
    }
    FirstNode->Dad = FirstNode->Suc;
    FirstNode->Cost = FirstNode->Suc->Cost;
    Max = LONG_MIN;
    do {
        if (N->V == -1) {
            Connect(N, Max, Sparse);
            if (N->NextCost > Max) {
                N1 = N;
                Max = N->NextCost;
            }
        }
    }
    while ((N = N->Suc) != FirstNode);
    N1->Next->V++;
    N1->V++;
    Sum += N1->NextCost;
    Norm = 0;
    do
        Norm += N->V * N->V;
    while ((N = N->Suc) != FirstNode);
    if (N1 == FirstNode)
        N1->Suc->Dad = 0;
    else {
        FirstNode->Dad = 0;
        Precede(N1, FirstNode);
        FirstNode = N1;
    }
    if (Norm == 0)
        for (N = FirstNode->Dad; N; N1 = N, N = N->Dad)
            Follow(N, N1);
    return Sum;
}
