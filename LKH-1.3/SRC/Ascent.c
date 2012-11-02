#include "LK.h"

/* 
   The Ascent function computes a lower bound on the optimal tour length using 
   subgradient optimization. The function also transforms the original problem 
   into a problem in which the alpha-values reflect the likelihood of edges being
   optimal.

   The function attempts to find penalties (pi-values) that maximizes the lower
   bound L(T(Pi)) - 2*PiSum, where L(T(Pi)) denotes the length of the minimum
   spanning 1-tree computed from the transformed distances, and PiSum denotes the 
   sum of pi-values. If C(i,j) denotes the length of and edge (i,j) then the 
   transformed distance D(i,j) of an edge is C(i,j) + Pi(i) + Pi(j).

   The Minimum1TreeCost function is used to compute the cost of a minimum 1-tree. 
   The Generatecandidates function is called in order to generate candidate sets. 
   Minimum 1-trees are then computed in the corresponding sparse graph.         
*/

double Ascent()
{
    Node *t;
    double BestW, W, W0;
    long T, Period, P;
    int InitialPhase;

  Start:
    /* Initialize Pi and BestPi */
    t = FirstNode;
    do
        t->BestPi = t->Pi = 0;
    while ((t = t->Suc) != FirstNode);

    /* Compute the cost of a minimum 1-tree */
    W = Minimum1TreeCost(0);

    /* Return this cost 
       if either
       (1) subgradient optimization is not wanted,
       (2) the norm of the tree (its deviation from a tour) is zero
       (in that case the true optimum has been found), or
       (3) the cost equals the specified value for optimum.
     */
    if (!Subgradient || !Norm || W / Precision == Optimum)
        return W;

    /* Generate symmetric candididate sets for all nodes */
    GenerateCandidates(AscentCandidates, LONG_MAX, 1);

    /* Set LastV of every node to V (the node's degree in the 1-tree) */
    t = FirstNode;
    do
        t->LastV = t->V;
    while ((t = t->Suc) != FirstNode);

    BestW = W0 = W;
    InitialPhase = 1;
    /* Perform subradient optimization with decreasing period length 
       and decreasing step size */
    for (Period = InitialPeriod, T = InitialStepSize * Precision; Period > 0 && T > 0 && Norm != 0; Period /= 2, T /= 2) {      /* Period and step size are halved at each iteration */
        if (TraceLevel >= 2) {
            printf("  T = %ld, Period = %ld, BestW = %0.2f, Norm = %ld\n",
                   T, Period, BestW / Precision, Norm);
            fflush(stdout);
        }
        for (P = 1; T && P <= Period && Norm != 0; P++) {
            /* Adjust the Pi-values */
            t = FirstNode;
            do {
                if (t->V != 0)
                    t->Pi += T * (7 * t->V + 3 * t->LastV) / 10;
                t->LastV = t->V;
            }
            while ((t = t->Suc) != FirstNode);
            /* Compute a minimum 1-tree in the sparse graph */
            W = Minimum1TreeCost(1);
            /* Test if an improvement has been found */
            if (W > BestW) {
                /* If the lower bound becomes greater than twice its
                   initial value it is taken as a sign that the graph is
                   too sparse */
                if (W > 2 * W0 && AscentCandidates < Dimension) {
                    W = Minimum1TreeCost(0);
                    if (W < W0) {
                        /* Double the number of candidate edges 
                           and start all over again */
                        if (TraceLevel >= 2) {
                            printf("Warning: AscentCandidates doubled\n");
                            fflush(stdout);
                        }
                        if ((AscentCandidates *= 2) > Dimension)
                            AscentCandidates = Dimension;
                        goto Start;
                    }
                    W0 = W;
                }
                BestW = W;
                /* Update the BestPi-values */
                t = FirstNode;
                do
                    t->BestPi = t->Pi;
                while ((t = t->Suc) != FirstNode);
                if (TraceLevel >= 2) {
                    printf
                        ("* T = %ld, Period = %ld, P = %ld, BestW = %0.2f, Norm = %ld\n",
                         T, Period, P, BestW / Precision, Norm);
                    fflush(stdout);
                }
                /* If in the initial phase, the step size is doubled */
                if (InitialPhase)
                    T *= 2;
                /* If the improvement was found at the last iteration of the current
                   period, then double the period */
                if (P == Period && (Period *= 2) > InitialPeriod)
                    Period = InitialPeriod;
            } else if (InitialPhase && P > Period / 2) {
                /* Conclude the initial phase */
                InitialPhase = 0;
                P = 0;
                T = 3 * T / 4;
            }
        }
    }

    t = FirstNode;
    do {
        free(t->CandidateSet);
        t->CandidateSet = 0;
        t->Pi = t->BestPi;
    }
    while ((t = t->Suc) != FirstNode);

    /* Compute a minimum 1-tree in the original graph */
    W = Minimum1TreeCost(0);

    if (TraceLevel >= 2) {
        printf("Ascent: BestW = %0.2f, Norm = %ld\n", BestW / Precision,
               Norm);
        fflush(stdout);
    }
    return W;
}
