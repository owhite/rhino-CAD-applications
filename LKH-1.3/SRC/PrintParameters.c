#include "LK.h"

/*
   The PrintParameters function prints the problem parameters to standard output. 
*/

void PrintParameters()
{
    int i;
    printf("\nPARAMETER_FILE = %s\n",
           ParameterFileName ? ParameterFileName : "");
    printf("ASCENT_CANDIDATES = %ld\n", AscentCandidates);
    printf("BACKTRACK_MOVE_TYPE = %d\n", BacktrackMoveType);
    printf("CANDIDATE_FILE = %s\n",
           CandidateFileName ? CandidateFileName : "");
    printf("EXCESS = %0.6f\n", Excess);
    printf("INITIAL_PERIOD = %ld\n", InitialPeriod);
    printf("INITIAL_STEP_SIZE = %ld\n", InitialStepSize);
    printf("INITIAL_TOUR_FILE = %s\n",
           InitialTourFileName ? InitialTourFileName : "");
    printf("INPUT_TOUR_FILE = %s\n",
           InputTourFileName ? InputTourFileName : "");
    printf("MAX_CANDIDATES = %ld", MaxCandidates);
    if (CandidateSetSymmetric)
        printf(" SYMMETRIC");
    printf("\n");
    printf("MAX_SWAPS = %ld\n", MaxSwaps);
    printf("MAX_TRIALS = %ld\n", MaxTrials);
    for (i = 0; i <= 1; i++)
        printf("MERGE_TOUR_FILE_%d = %s\n",
               i + 1, MergeTourFileName[i] ? MergeTourFileName[i] : "");
    printf("MOVE_TYPE = %d\n", MoveType);
    if (Optimum == -DBL_MAX)
        printf("OPTIMUM = -DBL_MAX\n");
    else
        printf("OPTIMUM = %0.0f\n", Optimum);
    printf("PI_FILE = %s\n", PiFileName ? PiFileName : "");
    printf("PRECISION = %ld\n", Precision);
    printf("PROBLEM_FILE = %s\n", ProblemFileName ? ProblemFileName : "");
    printf("RESTRICTED_SEARCH = %s\n", RestrictedSearch ? "YES" : "NO");
    printf("RUNS = %ld\n", Runs);
    printf("SEED = %ld\n", Seed);
    printf("SUBGRADIENT = %s\n", Subgradient ? "YES" : "NO");
    printf("TOUR_FILE = %s\n", TourFileName ? TourFileName : "");
    printf("TRACE_LEVEL = %d\n", TraceLevel);
    fflush(stdout);
}
