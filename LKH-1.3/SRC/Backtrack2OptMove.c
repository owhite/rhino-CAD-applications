#include "Segment.h"
#include "LK.h"

/*
   The Backtrack2OptMove function searches for a tour improvement using backtracking
   and initial 2-opt moves.  
   
   In case a 2-opt move is found that improves the tour, the improvement of the cost
   is made available to the caller through the parameter Gain. If *Gain > 0, an 
   improvement of the current tour has been found, and a pointer to the node that
   was connected to t1 (in order to close the tour) is returned. Otherwise, 0 is
   returned.

   The function is called from the LinKernighan function. 
*/

Node *Backtrack2OptMove(Node * t1, Node * t2, long *G0, long *Gain)
{
    Node *t3, *t4, *t;
    Candidate *Nt2;
    long G1, G2, G;

    if (SUC(t1) != t2)
        Reversed ^= 1;

    /* Choose (t2,t3) as a candidate edge emanating from t2 */
    for (Nt2 = t2->CandidateSet; t3 = Nt2->To; Nt2++) {
        if (t3 == t2->Pred || t3 == t2->Suc || 
            ((G1 = *G0 - Nt2->Cost) <= 0 &&
             ProblemType != HCP && ProblemType != HPP))
            continue;
        /* Choose t4 (only one choice gives a closed tour) */
        t4 = PRED(t3);
        if (Fixed(t3, t4))
            continue;
        G2 = G1 + C(t3, t4);
        if (!Forbidden(t4, t1) &&
            (!c || G2 - c(t4, t1) > 0) && (*Gain = G2 - C(t4, t1)) > 0) {
            Make2OptMove(t1, t2, t3, t4);
            return t4;
        }
        if (G2 - t4->Cost <= 0)
            continue;
        Make2OptMove(t1, t2, t3, t4);
        Exclude(t1, t2);
        Exclude(t3, t4);
        G = G2;
        t = t4;
        while (t = BestMove(t1, t, &G, Gain))
            if (*Gain > 0)
                return t;
        RestoreTour();
        if (t2 != SUC(t1))
            Reversed ^= 1;
    }
    *Gain = 0;
    return 0;
}
