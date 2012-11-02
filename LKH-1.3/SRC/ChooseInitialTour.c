#include "LK.h"

/*
   The ChooseInitialTour function generates a pseudo random initial tour. 
   The algorithm constructs a tour as follows. 

   First, a random node, N, is chosen.

   Then, as long as no all nodes have been chosen, choose the next node to 
   follow N in the tour, NextN, and set N equal to NextN.

   NextN is chosen as follows: 

		(A) If possible, choose NextN so that
			(N,NextN) is a candidate edge,
			the alpha-value of (N,NextN) is zero, and
			(N,NextN) belongs to the current best tour.
		(B) Otherwise, if possible, choose NextN such that 
			(N,NextN) is a candidate edge.
		(C) Otherwise, choose NextN among those nodes not already chosen.

   When more than one node may be chosen, the node is chosen at random 
   among the alternatives (a one-way list of nodes). 

   The sequence of chosen nodes constitutes the initial tour.
*/

void ChooseInitialTour()
{
    Node *N, *NextN, *FirstAlternative, *Last;
    Candidate *NN;
    long i;

    /* Choose a random node N = FirstFirstNode */
    N = FirstNode = &NodeSet[1 + rand() % Dimension];

    /* Mark all nodes as "not chosen" by setting their V field to zero */
    do
        N->V = 0;
    while ((N = N->Suc) != FirstNode);
    
    /* Choose FirstNode without two incident fixed edges */
    do {
        if (!N->FixedTo2)
            break;
    } while ((N = N->Suc) != FirstNode);
    FirstNode = N;
   
    /* Move nodes with two incident fixed edges before FirstNode */
    for (Last = FirstNode->Pred; N != Last; N = NextN) {
        NextN = N->Suc;
        if (N->FixedTo2)
            Follow(N, Last);
    }

    /* Mark FirstNode as chosen */
    FirstNode->V = 1;
    N = FirstNode;

    /* Loop as long as not all nodes have been chosen */
    while (N->Suc != FirstNode) {
        if (N->InitialSuc && Trial == 1)
            NextN = N->InitialSuc;
        else {
            for (NN = N->CandidateSet; NextN = NN->To; NN++)
                if (!NextN->V && Fixed(N, NextN))
                    break;
        }
        if (NextN == 0) {
            FirstAlternative = 0;
            i = 0;
            if (ProblemType != HCP && ProblemType != HPP) {
                /* Try case A0 */
                for (NN = N->CandidateSet; NextN = NN->To; NN++) {
                    if (!NextN->V && !NextN->FixedTo2 &&
                        Near(N, NextN) && IsCommonEdge(N, NextN)) {
                        i++;
                        NextN->Next = FirstAlternative;
                        FirstAlternative = NextN;
                    }
                }
            }
            if (i == 0 && MaxCandidates > 0 &&
                ProblemType != HCP && ProblemType != HPP) {
                /* Try case A */
                for (NN = N->CandidateSet; NextN = NN->To; NN++) {
                    if (!NextN->V && !NextN->FixedTo2 &&
                        NN->Alpha == 0 && InBestTour(N, NextN)) {
                        i++;
                        NextN->Next = FirstAlternative;
                        FirstAlternative = NextN;
                    }
                }
            }
            if (i == 0) {
                /* Try case B */
                for (NN = N->CandidateSet; NextN = NN->To; NN++) {
                    if (!NextN->V && !NextN->FixedTo2) {
                        i++;
                        NextN->Next = FirstAlternative;
                        FirstAlternative = NextN;
                    }
                }
            }
            if (i == 0) {
                /* Try case C (actually, not really a random choice) */
                NextN = N->Suc;
                while ((NextN->FixedTo2 || Forbidden(N, NextN))
                       && NextN->Suc != FirstNode)
                    NextN = NextN->Suc;
            } else {
                NextN = FirstAlternative;
                if (i > 1) {
                    /* Select NextN at random among the alternatives */
                    i = rand() % i;
                    while (i--)
                        NextN = NextN->Next;
                }
            }
        }
        /* Include NextN as the successor of N */
        Follow(NextN, N);
        N = NextN;
        N->V = 1;
    }
}
