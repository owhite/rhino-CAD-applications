#include "LK.h"

/*
   The PrintBestTour function prints the tour in TSPLIB format to the file 
   specified by TourFileName. 

   Nothing happens of TourFileName is 0.        
*/

void PrintBestTour()
{
    int i, n;

    if (TourFileName == 0)
        return;
    assert(TourFile = fopen(TourFileName, "w"));
    fprintf(TourFile, "NAME : %s.tour\n", Name);
    fprintf(TourFile, "COMMENT : Length = %0.0f\n", BestCost);
    fprintf(TourFile, "TYPE : TOUR\n");
    fprintf(TourFile, "DIMENSION : %d\n", Dimension);
    fprintf(TourFile, "TOUR_SECTION  \n");
    n = ProblemType != ATSP ? Dimension : Dimension / 2;
    for (i = 1; i <= n; i++)
        fprintf(TourFile, "%ld\n", BestTour[i]);
    fprintf(TourFile, "-1\nEOF\n");
    fclose(TourFile);
}
