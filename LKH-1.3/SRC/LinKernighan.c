#include "Segment.h"
#include "LK.h"

/*
   The LinKenighan function seeks to improve a tour by sequential and nonsequential
   edge exchanges.

   The function returns the cost of the resulting tour. 
*/

double LinKernighan()
{
    Node *t1, *t2, *SUCt1;
    long Gain, G0, i;
    double Cost;
    Candidate *Nt1;
    Segment *S;
    int X2;
    double LastTime = GetTime();

    Reversed = 0;
    S = FirstSegment;
    i = 0;
    do {
        S->Size = 0;
        S->Rank = ++i;
        S->Reversed = 0;
        S->First = S->Last = 0;
    }
    while ((S = S->Suc) != FirstSegment);
    i = 0;
    Hash = 0;
    Swaps = 0;
    FirstActive = LastActive = 0;

    /* Compute the cost of the initial tour, Cost.
       Compute the corresponding hash value, Hash.
       Initialize the segment list.
       Make all nodes "active" (so that they can be used as t1). */
    Cost = 0;
    t1 = FirstNode;
    do {
        t2 = t1->OldSuc = t1->Next = t1->Suc;
        t1->OldPred = t1->Pred;
        t1->Rank = ++i;
        Cost += C(t1, t2) - t1->Pi - t2->Pi;
        Hash ^= Rand[t1->Id] * Rand[t2->Id];
        t1->Cost = LONG_MAX;
        for (Nt1 = t1->CandidateSet; t2 = Nt1->To; Nt1++)
            if (t2 != t1->Pred && t2 != t1->Suc && Nt1->Cost < t1->Cost)
                t1->Cost = Nt1->Cost;
        t1->Parent = S;
        S->Size++;
        if (S->Size == 1)
            S->First = t1;
        S->Last = t1;
        if (S->Size == GroupSize)
            S = S->Suc;
        t1->OldPredExcluded = t1->OldSucExcluded = 0;
        t1->Next = 0;
        Activate(t1);
    }
    while ((t1 = t1->Suc) != FirstNode);
    if (HashSearch(HTable, Hash, Cost))
        return Cost / Precision;
    /* Loop as long as improvements are found */
    do {
        /* Choose t1 as the first "active" node */
        while (t1 = RemoveFirstActive()) {
            /* t1 is now "passive" */
            SUCt1 = SUC(t1);
            /* Choose t2 as one of t1's two neighbor nodes on the tour */
            for (X2 = 1; X2 <= 2; X2++) {
                t2 = X2 == 1 ? PRED(t1) : SUCt1;
                if ((RestrictedSearch && Near(t1, t2)) || Fixed(t1, t2))
                    continue;
                G0 = C(t1, t2);
                /* Make sequential moves */
                while (t2 = BacktrackMove ?
                       BacktrackMove(t1, t2, &G0, &Gain) :
                       BestMove(t1, t2, &G0, &Gain)) {
                    if (Gain > 0) {
                        /* An improvement has been found */
                        Cost -= Gain;
                        if (TraceLevel >= 3 ||
                            (TraceLevel == 2
                             && Cost / Precision < BetterCost)) {
                            printf("Cost = %0.0f, Time = %0.0f sec.\n",
                                   Cost / Precision, GetTime() - LastTime);
                            fflush(stdout);
                        }
                        StoreTour();
                        if (HashSearch(HTable, Hash, Cost))
                            goto End_LinKernighan;
                        /* Make t1 "active" again */
                        Activate(t1);
                        goto Next_t1;
                    }
                }
                RestoreTour();
            }
          Next_t1:;
        }
        if (!HashSearch(HTable, Hash, Cost))
            HashInsert(HTable, Hash, Cost);
        /* Attempt to find improvements using nonsequential moves (with Gain23) */
        if ((Gain = Gain23()) > 0) {
            /* An improvement has been found */
            Cost -= Gain;
            if (TraceLevel >= 3 ||
                (TraceLevel == 2 && Cost / Precision < BetterCost)) {
                printf("Cost = %0.0f, Time = %0.0f sec.\n",
                       Cost / Precision, GetTime() - LastTime);
                fflush(stdout);
            }
            StoreTour();
            if (HashSearch(HTable, Hash, Cost))
                goto End_LinKernighan;
        }
    }
    while (Gain > 0);

  End_LinKernighan:
    NormalizeNodeList();
    return Cost / Precision;
}
