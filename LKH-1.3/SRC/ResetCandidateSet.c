#include "LK.h"

/*
   Each time a trial has resulted in a shorter tour the candidate set is
   adjusted (by AdjustCandidateSet). The ResetCandidates function resets
   the candidate set. Any included edges are removed and the original
   order is re-established.

   The function is called at the end of the FindTour function.   
*/

void ResetCandidateSet()
{
    Candidate *NFrom, Temp, *NN;
    Node *From;

    From = FirstNode;
    /* Loop for all nodes */
    do {
        /* Reorder the candidate array of From */
        for (NFrom = From->CandidateSet + 1; NFrom->To; NFrom++) {
            if (InOptimumTour(From, NFrom->To))
                NFrom->Alpha = 0;
            Temp = *NFrom;
            for (NN = NFrom - 1;
                 NN >= From->CandidateSet &&
                 (Temp.Alpha < NN->Alpha ||
                  (Temp.Alpha == NN->Alpha && Temp.Cost < NN->Cost)); NN--)
                *(NN + 1) = *NN;
            *(NN + 1) = Temp;
        }
        NFrom--;
        /* Remove any included edges */
        while (NFrom->Alpha == LONG_MAX)
            NFrom--;
        NFrom++;
        NFrom->To = 0;
    }
    while ((From = From->Suc) != FirstNode);
}
