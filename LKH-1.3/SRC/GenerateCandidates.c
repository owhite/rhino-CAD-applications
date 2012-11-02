#include "LK.h"

/*
   The GenerateCandidates function associates to each node a set of incident 
   candidate edges. The candidate edges of each node are ordered according to
   their alpha-values.

   The parameter MaxCandidates specifies the maximum number of candidate edges 
   allowed for each node, and MaxAlpha puts an upper limit on their alpha-values.

   A non-zero value of Symmetric specifies that the candidate set is to be
   complemented such that every candidate edge is associated with both its two
   end nodes (in this way MaxCandidates may be exceeded). 

   The candidate edges of each node is kept in an array (CandidatSet) of
   structures. Each structure (Candidate) holds the following information:

   Node *To     : points to the other end node of the edge
   long Alpha   : contains the alpha-value of the edge
   long Cost    : the cost (length) of the edge

   The algorithm for computing alpha-values in time O(n^2) and space O(n) follows 
   the description in

   Keld Helsgaun,
   An Effective Implementation of the Lin-Kernighan Traveling Salesman Heuristic,
   Report, RUC, 1998. 
*/

#define Mark Next
#define Beta NextCost

static long Max(long a, long b)
{
    return a > b ? a : b;
}

void GenerateCandidates(const long MaxCandidates, const long MaxAlpha,
                        const int Symmetric)
{
    Node *From, *To;
    Candidate *NFrom, *NN, *NTo;
    long a, d, Count;

    /* Initialize CandidateSet for each node */
    From = FirstNode;
    do {
        free(From->CandidateSet);
        From->CandidateSet = 0;
        From->Mark = 0;
    }
    while ((From = From->Suc) != FirstNode);
    do {
        assert(From->CandidateSet =
               (Candidate *) malloc((MaxCandidates + 1) *
                                    sizeof(Candidate)));
        From->CandidateSet[0].To = 0;        
    }
    while ((From = From->Suc) != FirstNode);
    if (MaxCandidates <= 0)
        return;

    /* Loop for each node, From */
    do {
        NFrom = From->CandidateSet;
        if (From != FirstNode) {
            From->Beta = LONG_MIN;
            for (To = From; To->Dad != 0; To = To->Dad) {
                To->Dad->Beta =
                    !Fixed(To, To->Dad) ? Max(To->Beta, To->Cost)
                    : To->Beta;
                To->Dad->Mark = From;
            }
        }
        Count = 0;
        /* Loop for each node, To */
        To = FirstNode;
        do {
            if (To == From)
                continue;
            d = c && !Fixed(From, To) ? c(From, To) : D(From, To);
            if (From == FirstNode)
                a = To == From->Dad ? 0 : d - From->NextCost;
            else if (To == FirstNode)
                a = From == To->Dad ? 0 : d - To->NextCost;
            else {
                if (To->Mark != From)
                    To->Beta =
                        !Fixed(To, To->Dad) ? Max(To->Dad->Beta, To->Cost)
                        : To->Dad->Beta;
                a = d - To->Beta;
            }
            if (Fixed(From, To))
                a = LONG_MIN;
            else {
                if (To->Beta == LONG_MIN || From->FixedTo2 || To->FixedTo2
                    || Forbidden(From, To))
                    continue;
                if (InOptimumTour(From, To)) {
                    a = 0;
                    if (c)
                        d = D(From, To);
                } else if (c) {
                    if (a > MaxAlpha ||
                        (Count == MaxCandidates &&
                         (a > (NFrom - 1)->Alpha ||
                          (a == (NFrom - 1)->Alpha
                           && d >= (NFrom - 1)->Cost))))
                        continue;
                    if (To == From->Dad) {
                        d = From->Cost;
                        a = 0;
                    } else if (From == To->Dad) {
                        d = To->Cost;
                        a = 0;
                    } else {
                        a -= d;
                        a += (d = D(From, To));
                    }
                }
            }
            if (a <= MaxAlpha) {
                /* Insert new candidate edge in From->CandidateSet */
                NN = NFrom;
                while (--NN >= From->CandidateSet) {
                    if (a > NN->Alpha || (a == NN->Alpha && d >= NN->Cost))
                        break;
                    *(NN + 1) = *NN;
                }
                NN++;
                NN->To = To;
                NN->Cost = d;
                NN->Alpha = a;
                if (Count < MaxCandidates) {
                    Count++;
                    NFrom++;
                }
                NFrom->To = 0;
            }
        }
        while ((To = To->Suc) != FirstNode);
    }
    while ((From = From->Suc) != FirstNode);

    if (!Symmetric)
        return;

    /* Complement the candidate set such that every candidate edge is 
       associated with both its two end nodes */
    To = FirstNode;
    do {
        for (NTo = To->CandidateSet; From = NTo->To; NTo++) {
            Count = 0;
            for (NN = NFrom = From->CandidateSet; NN->To && NN->To != To;
                 NN++)
                Count++;
            if (!NN->To) {
                a = NTo->Alpha;
                d = NTo->Cost;
                while (--NN >= NFrom) {
                    if (a > NN->Alpha || (a == NN->Alpha && d >= NN->Cost))
                        break;
                    *(NN + 1) = *NN;
                }
                NN++;
                NN->To = To;
                NN->Cost = d;
                NN->Alpha = a;
                assert(From->CandidateSet =
                       (Candidate *) realloc(From->CandidateSet,
                                             (Count +
                                              2) * sizeof(Candidate)));
                From->CandidateSet[Count + 1].To = 0;
            }
        }
    }
    while ((To = To->Suc) != FirstNode);
}
