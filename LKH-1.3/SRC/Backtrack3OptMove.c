#include "Segment.h"
#include "LK.h"

/* 
   The Backtrack3OptMove function searches for a tour improvement using backtracking
   and initial r-opt moves (2 <= r <= 3).  
   
   In case a r-opt move is found that improves the tour, the improvement of the cost
   is made available to the caller through the parameter Gain. If *Gain > 0, an 
   improvement of the current tour has been found, and a pointer to the node that
   was connected to t1 (in order to close the tour) is returned. Otherwise, 0 is
   returned.

   The function is called from the LinKernighan function.   
*/

Node *Backtrack3OptMove(Node * t1, Node * t2, long *G0, long *Gain)
{
    Node *t3, *t4, *t5, *t6, *t;
    Candidate *Nt2, *Nt4;
    long G1, G2, G3, G4, G;
    int Case6, X4, X6;

    if (SUC(t1) != t2)
        Reversed ^= 1;

    /* Choose (t2,t3) as a candidate edge emanating from t2 */
    for (Nt2 = t2->CandidateSet; t3 = Nt2->To; Nt2++) {
        if (t3 == t2->Pred || t3 == t2->Suc || 
            ((G1 = *G0 - Nt2->Cost) <= 0 &&
             ProblemType != HCP && ProblemType != HPP))
            continue;
        /* Choose t4 as one of t3's two neighbors on the tour */
        for (X4 = 1; X4 <= 2; X4++) {
            t4 = X4 == 1 ? PRED(t3) : SUC(t3);
            if (Fixed(t3, t4))
                continue;
            G2 = G1 + C(t3, t4);
            if (X4 == 1) {
                if (!Forbidden(t4, t1) &&
                    (!c || G2 - c(t4, t1) > 0) &&
                    (*Gain = G2 - C(t4, t1)) > 0) {
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
            /* Choose (t4,t5) as a candidate edge emanating from t4 */
            for (Nt4 = t4->CandidateSet; t5 = Nt4->To; Nt4++) {
                if (t5 == t4->Pred || t5 == t4->Suc ||
                    (G3 = G2 - Nt4->Cost) <= 0 ||
                    (X4 == 2 && !BETWEEN(t2, t5, t3)))
                    continue;
                /* Choose t6 as one of t5's two neighbors on the tour */
                for (X6 = 1; X6 <= X4; X6++) {
                    if (X4 == 1) {
                        Case6 = 1 + !BETWEEN(t2, t5, t4);
                        t6 = Case6 == 1 ? SUC(t5) : PRED(t5);
                    } else {
                        Case6 = 4 + X6;
                        t6 = X6 == 1 ? SUC(t5) : PRED(t5);
                        if (t6 == t1)
                            continue;
                    }
                    if (Fixed(t5, t6))
                        continue;
                    G4 = G3 + C(t5, t6);
                    if (!Forbidden(t6, t1) &&
                        (!c || G4 - c(t6, t1) > 0) &&
                        (*Gain = G4 - C(t6, t1)) > 0) {
                        Make3OptMove(t1, t2, t3, t4, t5, t6, Case6);
                        return t6;
                    }
                    if (G4 - t6->Cost <= 0)
                        continue;
                    Make3OptMove(t1, t2, t3, t4, t5, t6, Case6);
                    Exclude(t1, t2);
                    Exclude(t3, t4);
                    Exclude(t5, t6);
                    G = G4;
                    t = t6;
                    while (t = BestMove(t1, t, &G, Gain))
                        if (*Gain > 0)
                            return t;
                    RestoreTour();
                    if (t2 != SUC(t1))
                        Reversed ^= 1;
                }
            }
        }
    }
    *Gain = 0;
    return 0;
}
