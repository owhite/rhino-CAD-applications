#include "Segment.h"
#include "LK.h"

/*
   The Backtrack4OptMove function searches for a tour improvement using backtracking
   and initial r-opt moves (2 <= r <= 4).  
   
   In case a r-opt move is found that improves the tour, the improvement of the cost
   is made available to the caller through the parameter Gain. If *Gain > 0, an 
   improvement of the current tour has been found, and a pointer to the node that
   was connected to t1 (in order to close the tour) is returned. Otherwise, 0 is
   returned.

   The function is called from the LinKernighan function.   
*/

Node *Backtrack4OptMove(Node * t1, Node * t2, long *G0, long *Gain)
{
    Candidate *Nt2, *Nt4, *Nt6;
    Node *t3, *t4, *t5, *t6, *t7, *t8, *t;
    long G1, G2, G3, G4, G5, G6, G;
    int Case6, Case8, X4, X6, X8;

    *Gain = 0;
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
                    (G3 = G2 - Nt4->Cost) <= 0)
                    continue;
                /* Choose t6 as one of t5's two neighbors on the tour */
                for (X6 = 1; X6 <= 2; X6++) {
                    if (X4 == 1) {
                        if (X6 == 1) {
                            Case6 = 1 + !BETWEEN(t2, t5, t4);
                            t6 = Case6 == 1 ? SUC(t5) : PRED(t5);
                        } else {
                            t6 = t6 == t5->Pred ? t5->Suc : t5->Pred;
                            if ((t5 == t1 && t6 == t2) ||
                                (t5 == t2 && t6 == t1))
                                continue;
                            Case6 += 2;
                        }
                    } else if (BETWEEN(t2, t5, t3)) {
                        Case6 = 4 + X6;
                        t6 = X6 == 1 ? SUC(t5) : PRED(t5);
                        if (t6 == t1)
                            continue;
                    } else {
                        if (X6 == 2)
                            break;
                        Case6 = 7;
                        t6 = X6 == 1 ? PRED(t5) : SUC(t5);
                        if (t6 == t2)
                            continue;
                    }
                    if (Fixed(t5, t6))
                        continue;
                    G4 = G3 + C(t5, t6);
                    if (Case6 <= 2 || Case6 == 5 || Case6 == 6) {
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
                    /* Choose (t6,t7) as a candidate edge emanating from t6 */
                    for (Nt6 = t6->CandidateSet; t7 = Nt6->To; Nt6++) {
                        if (t7 == t6->Pred || t7 == t6->Suc ||
                            (t6 == t2 && t7 == t3) ||
                            (t6 == t3 && t7 == t2) ||
                            (G5 = G4 - Nt6->Cost) <= 0)
                            continue;
                        /* Choose t8 as one of t7's two neighbors on the tour */
                        for (X8 = 1; X8 <= 2; X8++) {
                            if (X8 == 1) {
                                Case8 = Case6;
                                t8 = 0;
                                switch (Case6) {
                                case 1:
                                    t8 = BETWEEN(t2, t7,
                                                 t5) ? SUC(t7) : PRED(t7);
                                    break;
                                case 2:
                                    t8 = BETWEEN(t3, t7,
                                                 t6) ? SUC(t7) : PRED(t7);
                                    break;
                                case 3:
                                    if (BETWEEN(t5, t7, t4))
                                        t8 = SUC(t7);
                                    break;
                                case 4:
                                    if (BETWEEN(t2, t7, t5))
                                        t8 = BETWEEN(t2, t7,
                                                     t4) ? SUC(t7) :
                                            PRED(t7);
                                    break;
                                case 5:
                                    t8 = PRED(t7);
                                    break;
                                case 6:
                                    t8 = BETWEEN(t2, t7,
                                                 t3) ? SUC(t7) : PRED(t7);
                                    break;
                                case 7:
                                    if (BETWEEN(t2, t7, t3))
                                        t8 = SUC(t7);
                                    break;
                                }
                                if (t8 == 0)
                                    break;
                            } else {
                                if (Case6 != 3 && Case6 != 4 && Case6 != 7)
                                    break;
                                t8 = t8 == t7->Pred ? t7->Suc : t7->Pred;
                                Case8 += 8;
                            }
                            if (t8 == t1 ||
                                (t7 == t3 && t8 == t4) ||
                                (t7 == t4 && t8 == t3))
                                continue;
                            if (Fixed(t7, t8))
                                continue;
                            G6 = G5 + C(t7, t8);
                            if (t8 != t1) {
                                if (!Forbidden(t8, t1)
                                    && (!c || G6 - c(t8, t1) > 0)
                                    && (*Gain = G6 - C(t8, t1)) > 0) {
                                    Make4OptMove(t1, t2, t3, t4, t5, t6,
                                                 t7, t8, Case8);
                                    return t8;
                                }
                                if (G6 - t8->Cost <= 0)
                                    continue;
                                Make4OptMove(t1, t2, t3, t4, t5, t6, t7,
                                             t8, Case8);
                                Exclude(t1, t2);
                                Exclude(t3, t4);
                                Exclude(t5, t6);
                                Exclude(t7, t8);
                                G = G6;
                                t = t8;
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
            }
        }
    }
    *Gain = 0;
    return 0;
}
