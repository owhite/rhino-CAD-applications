#include "LK.h"
#include "Heap.h"

/*      
   The FreeStructures function frees all allocated structures.
*/

void FreeStructures()
{
    if (FirstNode) {
        Node *N = FirstNode, *Next;
        do {
            Next = N->Suc;
            free(N->CandidateSet);
        } while ((N = Next) != FirstNode);
        FirstNode = 0;
    }
    if (FirstSegment) {
        Segment *S = FirstSegment, *SPrev;
        do {
            SPrev = S->Pred;
            free(S);
        } while ((S = SPrev) != FirstSegment);
        FirstSegment = 0;

    }
    free(NodeSet);
    NodeSet = 0;
    free(CostMatrix);
    CostMatrix = 0;
    free(BestTour);
    BestTour = 0;
    free(BetterTour);
    BetterTour = 0;
    free(SwapStack);
    SwapStack = 0;
    free(HTable);
    HTable = 0;
    free(Rand);
    Rand = 0;
    free(CacheSig);
    CacheSig = 0;
    free(CacheVal);
    CacheVal = 0;
    free(Heap);
    Heap = 0;
    free(Name);
    Name = 0;
    free(Type);
    Type = 0;
    free(EdgeWeightType);
    EdgeWeightType = 0;
    free(EdgeWeightFormat);
    EdgeWeightFormat = 0;
    free(EdgeDataFormat);
    EdgeDataFormat = 0;
    free(NodeCoordType);
    NodeCoordType = 0;
    free(DisplayDataType);
    DisplayDataType = 0;
}
