#include "LK.h"

/*
   The RecordBestTour function records the current best tour in the BestTour 
   array.

   The function is called by LKmain each time a run has resulted in a
   shorter tour. Thus when the predetermined number of runs have been is
   completed, BestTour contains an array representation of the best tour
   found.    
*/

void RecordBestTour()
{
    long i;

    for (i = 1; i <= Dimension; i++)
        BestTour[i] = BetterTour[i];
}
