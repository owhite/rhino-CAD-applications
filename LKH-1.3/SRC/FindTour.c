#include "LK.h"

/*
   After the candidate set has been created the FindTour function is called a 
   predetermined number of times (Runs). 

   FindTour performs a number of trials, where in each trial it attempts to 
   improve a chosen initial tour using the modified Lin-Kernighan edge exchange 
   heuristics. 

   Each time a better tour is found, the tour is recorded, and the candidates are 
   reorderded by the AdjustCandidateSet function. Precedence is given to edges that 
   are common to two currently best tours. The candidate set is extended with those
   tour edges that are not present in the current set. The original candidate set
   is re-established at exit from FindTour.  
*/

double FindTour()
{
    double Cost;
    Node *t;
    double LastTime = GetTime();

    t = FirstNode;
    do
        t->OldPred = t->OldSuc = t->NextBestSuc = t->BestSuc = 0;
    while ((t = t->Suc) != FirstNode);
    HashInitialize(HTable);
    BetterCost = DBL_MAX;
    for (Trial = 1; Trial <= MaxTrials; Trial++) {
        ChooseInitialTour();
        Cost = LinKernighan();
        if (Cost < BetterCost) {
            if (TraceLevel >= 1) {
                printf("* %ld: Cost = %0.0f, Time = %0.0f sec.\n",
                       Trial, Cost, GetTime() - LastTime);
                fflush(stdout);
            }
            BetterCost = Cost;
            RecordBetterTour();
            if (BetterCost <= Optimum)
                break;
            AdjustCandidateSet();
            HashInitialize(HTable);
            HashInsert(HTable, Hash, Cost * Precision);
        } else if (TraceLevel >= 2) {
            printf("  %ld: Cost = %0.0f, Time = %0.0f sec.\n",
                   Trial, Cost, GetTime() - LastTime);
            fflush(stdout);
        }
    }
    if (Trial > MaxTrials)
        Trial = MaxTrials;
    ResetCandidateSet();
    return BetterCost;
}
