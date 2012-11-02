#include "Segment.h"
#include "LK.h"

/*
   The Backtrack5OptMove function searches for a tour improvement using backtracking
   and initial r-opt moves (2 <= r <= 5).  
   
   In case a r-opt move is found that improves the tour, the improvement of the cost
   is made available to the caller through the parameter Gain. If *Gain > 0, an 
   improvement of the current tour has been found, and a pointer to the node that
   was connected to t1 (in order to close the tour) is returned. Otherwise, 0 is
   returned.

   The function is called from the LinKernighan function. 
*/

Node *Backtrack5OptMove(Node * t1, Node * t2, long *G0, long *Gain)
{
    Node *t3, *t4, *t5, *t6, *t7, *t8, *t9, *t10, *t;
    Candidate *Nt2, *Nt4, *Nt6, *Nt8;
    long G1, G2, G3, G4, G5, G6, G7, G8, G;
    int Case6, Case8, Case10, X4, X6, X8, X10, BTW275, BTW674, BTW571,
        BTW376, BTW574, BTW671, BTW471, BTW673, BTW573, BTW273;

    if (t2 != SUC(t1))
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
                if (t5 == t4->Pred || t5 == t4->Suc
                    || (G3 = G2 - Nt4->Cost) <= 0)
                    continue;
                /* Choose t6 as one of t5's two neighbors on the tour */
                for (X6 = 1; X6 <= 2; X6++) {
                    if (X4 == 1) {
                        if (X6 == 1) {
                            Case6 = 1 + !BETWEEN(t2, t5, t4);
                            t6 = Case6 == 1 ? SUC(t5) : PRED(t5);
                        } else {
                            t6 = t6 == t5->Pred ? t5->Suc : t5->Pred;
                            if ((t5 == t1 && t6 == t2)
                                || (t5 == t2 && t6 == t1))
                                continue;
                            Case6 += 2;
                        }
                    } else if (BETWEEN(t2, t5, t3)) {
                        Case6 = 4 + X6;
                        t6 = X6 == 1 ? SUC(t5) : PRED(t5);
                        if (t6 == t1)
                            continue;
                    } else {
                        Case6 = 6 + X6;
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
                        if (t7 == t6->Pred || t7 == t6->Suc
                            || (t6 == t2 && t7 == t3) || (t6 == t3
                                                          && t7 == t2)
                            || (G5 = G4 - Nt6->Cost) <= 0)
                            continue;
                        /* Choose t8 as one of t7's two neighbors on the tour */
                        for (X8 = 1; X8 <= 2; X8++) {
                            if (X8 == 1) {
                                Case8 = Case6;
                                switch (Case6) {
                                case 1:
                                    if (BTW275 = BETWEEN(t2, t7, t5))
                                        t8 = SUC(t7);
                                    else {
                                        t8 = PRED(t7);
                                        BTW674 = BETWEEN(t6, t7, t4);
                                    }
                                    break;
                                case 2:
                                    if (BTW376 = BETWEEN(t3, t7, t6))
                                        t8 = SUC(t7);
                                    else {
                                        t8 = PRED(t7);
                                        BTW571 = BETWEEN(t5, t7, t1);
                                    }
                                    break;
                                case 3:
                                    t8 = SUC(t7);
                                    BTW574 = BETWEEN(t5, t7, t4);
                                    break;
                                case 4:
                                    if (BTW671 = BETWEEN(t6, t7, t1))
                                        t8 = PRED(t7);
                                    else
                                        t8 = BETWEEN(t2, t7,
                                                     t4) ? SUC(t7) :
                                            PRED(t7);
                                    break;
                                case 5:
                                    t8 = PRED(t7);
                                    BTW471 = BETWEEN(t4, t7, t1);
                                    if (!BTW471)
                                        BTW673 = BETWEEN(t6, t7, t3);
                                    break;
                                case 6:
                                    if (BTW471 = BETWEEN(t4, t7, t1))
                                        t8 = PRED(t7);
                                    else {
                                        t8 = SUC(t7);
                                        BTW573 = BETWEEN(t5, t7, t3);
                                    }
                                    break;
                                case 7:
                                case 8:
                                    t8 = SUC(t7);
                                    BTW273 = BETWEEN(t2, t7, t3);
                                    break;
                                }
                            } else {
                                t8 = t8 == t7->Pred ? t7->Suc : t7->Pred;
                                Case8 += 8;
                            }
                            if ((t7 == t1 && t8 == t2)
                                || (t7 == t2 && t8 == t1)
                                || (t7 == t3 && t8 == t4)
                                || (t7 == t4 && t8 == t3))
                                continue;
                            if (Fixed(t7, t8))
                                continue;
                            if (Case6 == 3 && !BTW574
                                && (X8 == 1) == BETWEEN(t3, t7, t1))
                                continue;
                            if (Case6 == 4 && BTW671 && X8 == 2)
                                break;
                            if (Case6 == 7 && !BTW273
                                && (X8 == 1) == BETWEEN(t5, t7, t1))
                                continue;
                            if (Case6 == 8 && !BTW273
                                && !BETWEEN(t4, t7, t5))
                                break;
                            G6 = G5 + C(t7, t8);
                            if (t8 != t1
                                && (Case6 == 3 ? BTW574 : Case6 ==
                                    4 ? !BTW671 : Case6 ==
                                    7 ? BTW273 : Case6 != 8 && X8 == 1)) {
                                if (!Forbidden(t8, t1)
                                    && (!c || G6 - c(t8, t1) > 0)
                                    && (*Gain = G6 - C(t8, t1)) > 0) {
                                    Make4OptMove(t1, t2, t3, t4, t5, t6,
                                                 t7, t8, Case8);
                                    return t8;
                                }
                                if (G8 - t8->Cost <= 0)
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
                            /* Choose (t8,t9) as a candidate edge emanating from t8 */
                            for (Nt8 = t8->CandidateSet; t9 = Nt8->To;
                                 Nt8++) {
                                if (t9 == t8->Pred || t9 == t8->Suc
                                    || t9 == t1 || (t8 == t2 && t9 == t3)
                                    || (t8 == t3 && t9 == t2)
                                    || (t8 == t4 && t9 == t5)
                                    || (t8 == t5 && t9 == t4)
                                    || (G7 = G6 - Nt8->Cost) <= 0)
                                    continue;
                                /* Choose t10 as one of t9's two neighbors on the tour */
                                for (X10 = 1; X10 <= 2; X10++) {
                                    if (X10 == 1) {
                                        t10 = 0;
                                        switch (Case8) {
                                        case 1:
                                            t10 =
                                                (BTW275 ?
                                                 BETWEEN(t8, t9, t5)
                                                 || BETWEEN(t3, t9,
                                                            t1) : BTW674 ?
                                                 BETWEEN(t7, t9,
                                                         t1) : BETWEEN(t7,
                                                                       t9,
                                                                       t5))
                                                ? PRED(t9)
                                                : SUC(t9);
                                            Case10 = 22;
                                            break;
                                        case 2:
                                            t10 =
                                                (BTW376 ?
                                                 BETWEEN(t8, t9,
                                                         t4) : BTW571 ?
                                                 BETWEEN(t7, t9, t1)
                                                 || BETWEEN(t3, t9,
                                                            t6) :
                                                 BETWEEN(t7, t9,
                                                         t1)) ? PRED(t9)
                                                : SUC(t9);
                                            Case10 = 23;
                                            break;
                                        case 3:
                                            if (BTW574) {
                                                t10 =
                                                    BETWEEN(t5, t9,
                                                            t1) ? PRED(t9)
                                                    : SUC(t9);
                                                Case10 = 24;
                                                break;
                                            }
                                            if (!BETWEEN(t5, t9, t4))
                                                break;
                                            t10 = SUC(t9);
                                            Case10 = 1;
                                            break;
                                        case 4:
                                            if (BTW671) {
                                                if (!BETWEEN(t2, t9, t5))
                                                    break;
                                                t10 = SUC(t9);
                                                Case10 = 2;
                                                break;
                                            }
                                            t10 =
                                                BETWEEN(t6, t9,
                                                        t4) ? PRED(t9) :
                                                SUC(t9);
                                            Case10 = 25;
                                            break;
                                        case 5:
                                            t10 =
                                                (BTW471 ?
                                                 BETWEEN(t7, t9,
                                                         t1) : BTW673 ?
                                                 BETWEEN(t7, t9,
                                                         t5) : BETWEEN(t4,
                                                                       t9,
                                                                       t1)
                                                 || BETWEEN(t7, t9,
                                                            t5)) ? PRED(t9)
                                                : SUC(t9);
                                            Case10 = 26;
                                            break;
                                        case 6:
                                            t10 =
                                                (BTW471 ?
                                                 BETWEEN(t7, t9,
                                                         t3) : BTW573 ?
                                                 BETWEEN(t8, t9,
                                                         t6) : BETWEEN(t4,
                                                                       t9,
                                                                       t1)
                                                 || BETWEEN(t8, t9,
                                                            t6)) ? PRED(t9)
                                                : SUC(t9);
                                            Case10 = 27;
                                            break;
                                        case 7:
                                            if (BTW273) {
                                                t10 =
                                                    BETWEEN(t5, t9,
                                                            t3) ? PRED(t9)
                                                    : SUC(t9);
                                                Case10 = 28;
                                                break;
                                            }
                                            if (!BETWEEN(t2, t9, t3))
                                                break;
                                            t10 = SUC(t9);
                                            Case10 = 3;
                                            break;
                                        case 8:
                                            if (BTW273) {
                                                if (!BETWEEN(t4, t9, t5))
                                                    break;
                                                Case10 = 4;
                                            } else {
                                                if (!BETWEEN(t2, t9, t3))
                                                    break;
                                                Case10 = 5;
                                            }
                                            t10 = SUC(t9);
                                            break;
                                        case 9:
                                            if (BTW275) {
                                                if (!BETWEEN(t7, t9, t4))
                                                    break;
                                                t10 = SUC(t9);
                                                Case10 = 6;
                                                break;
                                            }
                                            if (!BTW674) {
                                                if (!BETWEEN(t2, t9, t7))
                                                    break;
                                                t10 = SUC(t9);
                                                Case10 = 7;
                                                break;
                                            }
                                            if (!BETWEEN(t6, t9, t7))
                                                break;
                                            t10 = SUC(t9);
                                            Case10 = 8;
                                            break;
                                        case 10:
                                            if (BTW376) {
                                                if (!BETWEEN(t7, t9, t6))
                                                    break;
                                                t10 = SUC(t9);
                                                Case10 = 9;
                                                break;
                                            }
                                            if (BTW571) {
                                                if (!BETWEEN(t2, t9, t7))
                                                    break;
                                                t10 = SUC(t9);
                                                Case10 = 10;
                                                break;
                                            }
                                            if (!BETWEEN(t3, t9, t6)
                                                && !BETWEEN(t2, t9, t7))
                                                break;
                                            t10 = SUC(t9);
                                            Case10 = 11;
                                            break;
                                        case 11:
                                            if (BTW574) {
                                                t10 =
                                                    BETWEEN(t3, t9,
                                                            t1) ? PRED(t9)
                                                    : SUC(t9);
                                                Case10 = 29;
                                                break;
                                            }
                                            if (!BETWEEN(t5, t9, t4))
                                                break;
                                            t10 = SUC(t9);
                                            Case10 = 12;
                                            break;
                                        case 12:
                                            t10 =
                                                BETWEEN(t3, t9,
                                                        t1) ? PRED(t9) :
                                                SUC(t9);
                                            Case10 = 30;
                                            break;
                                        case 13:
                                            if (BTW471) {
                                                if (!BETWEEN(t2, t9, t7))
                                                    break;
                                                t10 = SUC(t9);
                                                Case10 = 13;
                                                break;
                                            }
                                            if (BTW673) {
                                                if (!BETWEEN(t6, t9, t7))
                                                    break;
                                                t10 = SUC(t9);
                                                Case10 = 14;
                                                break;
                                            }
                                            if (!BETWEEN(t6, t9, t3)
                                                && !BETWEEN(t2, t9, t7))
                                                break;
                                            t10 = SUC(t9);
                                            Case10 = 15;
                                            break;
                                        case 14:
                                            if (BTW471) {
                                                if (!BETWEEN(t2, t9, t7))
                                                    break;
                                                t10 = SUC(t9);
                                                Case10 = 16;
                                                break;
                                            }
                                            if (BTW573) {
                                                if (!BETWEEN(t7, t9, t3)
                                                    && !BETWEEN(t2, t9,
                                                                t6))
                                                    break;
                                                t10 = SUC(t9);
                                                Case10 = 17;
                                                break;
                                            }
                                            if (!BETWEEN(t7, t9, t6))
                                                break;
                                            t10 = SUC(t9);
                                            Case10 = 18;
                                            break;
                                        case 15:
                                            if (BTW273) {
                                                t10 =
                                                    BETWEEN(t5, t9,
                                                            t1) ? PRED(t9)
                                                    : SUC(t9);
                                                Case10 = 31;
                                                break;
                                            }
                                            if (!BETWEEN(t2, t9, t3))
                                                break;
                                            t10 = SUC(t9);
                                            Case10 = 19;
                                            break;
                                        case 16:
                                            if (BTW273) {
                                                if (!BETWEEN(t4, t9, t5))
                                                    break;
                                                Case10 = 20;
                                            } else {
                                                if (!BETWEEN(t2, t9, t3))
                                                    break;
                                                Case10 = 21;
                                            }
                                            t10 = SUC(t9);
                                            break;
                                        }
                                        if (!t10)
                                            break;
                                    } else {
                                        if (Case10 >= 22)
                                            continue;
                                        Case10 += 31;
                                        t10 =
                                            t10 ==
                                            t9->Pred ? t9->Suc : t9->Pred;
                                    }
                                    if (t10 == t1
                                        || (t9 == t3 && t10 == t4)
                                        || (t9 == t4 && t10 == t3)
                                        || (t9 == t5 && t10 == t6)
                                        || (t9 == t6 && t10 == t5))
                                        continue;
                                    if (Fixed(t9, t10))
                                        continue;
                                    G8 = G7 + C(t9, t10);
                                    if (!Forbidden(t10, t1)
                                        && (!c || G8 - c(t10, t1) > 0)
                                        && (*Gain = G8 - C(t10, t1)) > 0) {
                                        Make5OptMove(t1, t2, t3, t4, t5,
                                                     t6, t7, t8, t9, t10,
                                                     Case10);
                                        return t10;
                                    }
                                    if (G8 - t10->Cost <= 0)
                                        continue;
                                    Make5OptMove(t1, t2, t3, t4, t5, t6,
                                                 t7, t8, t9, t10, Case10);
                                    Exclude(t1, t2);
                                    Exclude(t3, t4);
                                    Exclude(t5, t6);
                                    Exclude(t7, t8);
                                    Exclude(t9, t10);
                                    G = G8;
                                    t = t10;
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
    }
    *Gain = 0;
    return 0;
}
