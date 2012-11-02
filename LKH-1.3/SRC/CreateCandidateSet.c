#include "LK.h"

/*
   The CreateCandidateSet function determines for each node its set of incident
   candidate edges.

   The Ascent function is called to determine a lower bound on the optimal tour 
   using subgradient optimization. But only if the penalties (the pi-values) is
   not available on file. In the latter case, the penalties is read from the file,
   and the lower bound is computed from a minimum 1-tree.      

   The function GenerateCandidates is called to compute the alpha-values and to 
   associate to each node a set of incident candidate edges.  

   The CreateCandidateSet function itself is called from LKmain.
*/

void CreateCandidateSet()
{
    double Cost;
    long i, j, Id, Count, Alpha;
    Node *Na, *Nb;
    Candidate *NNa, *NNb;
    double LastTime = GetTime();

    if (ProblemType == HPP) {
        Norm = 9999;
        return;
    }
    if (C == C_EXPLICIT) {
        Na = FirstNode;
        do {
            for (i = 1; i < Na->Id; i++)
                Na->C[i] *= Precision;
        }
        while ((Na = Na->Suc) != FirstNode);
    }
    if (PiFileName == 0 || (PiFile = fopen(PiFileName, "r")) == 0) {
        /* No PiFile specified or available */
        Cost = Ascent();
        if (PiFileName && (PiFile = fopen(PiFileName, "w"))) {
            Na = FirstNode;
            do
                fprintf(PiFile, "%ld %ld\n", Na->Id, Na->Pi);
            while ((Na = Na->Suc) != FirstNode);
            fclose(PiFile);
        }
    } else {
        /* Read the Pi-values from file */
        fscanf(PiFile, "%ld", &Id);
        assert(Id >= 1 && Id <= Dimension);
        FirstNode = Na = &NodeSet[Id];
        fscanf(PiFile, "%ld", &Na->Pi);
        for (i = 2; i <= Dimension; i++) {
            fscanf(PiFile, "%ld", &Id);
            assert(Id >= 1 && Id <= Dimension);
            Nb = &NodeSet[Id];
            fscanf(PiFile, "%ld", &Nb->Pi);
            Nb->Pred = Na;
            Na->Suc = Nb;
            Na = Nb;
        }
        FirstNode->Pred = Nb;
        Nb->Suc = FirstNode;
        fclose(PiFile);
        if (CandidateFileName == 0 ||
            (CandidateFile = fopen(CandidateFileName, "r")) == 0)
            Cost = Minimum1TreeCost(0);
        else {
            if (MaxCandidates == 0) {
                Na = FirstNode;
                do {
                    Na->CandidateSet =
                        (Candidate *) malloc(sizeof(Candidate));
                    Na->CandidateSet[0].To = 0;
                } while ((Na = Na->Suc) != FirstNode);
            } else {
                for (i = 1; i <= Dimension; i++) {
                    fscanf(CandidateFile, "%ld", &Id);
                    assert(Id >= 1 && Id <= Dimension);
                    Na = &NodeSet[Id];
                    fscanf(CandidateFile, "%ld", &Id);
                    assert(Id >= 0 && Id <= Dimension);
                    Na->Dad = Id ? &NodeSet[Id] : 0;
                    assert(Na != Na->Dad);
                    fscanf(CandidateFile, "%ld", &Count);
                    Na->CandidateSet =
                        (Candidate *) malloc(((Count < MaxCandidates ? Count : MaxCandidates) + 1) *
                                             sizeof(Candidate));
                    for (j = 0, NNa = Na->CandidateSet; j < Count; j++) {
                        fscanf(CandidateFile, "%ld", &Id);
                        assert(Id >= 0 && Id <= Dimension);
                        fscanf(CandidateFile, "%ld", &Alpha);
                        if (j < MaxCandidates) {
                            NNa->To = &NodeSet[Id];
                            NNa->Cost = D(Na, NNa->To);
                            NNa->Alpha = Alpha;
                            NNa++;
                        }
                    }
                    NNa->To = 0;
                }
            }
            fclose(CandidateFile);
            Norm = 9999;
            goto End_CreateCandidateSet;
        }
    }
    LowerBound = Cost / Precision;
    printf("\nLower bound = %0.1f, ", LowerBound);
    if (Optimum != -DBL_MAX && Optimum != 0)
        printf("Gap = %0.1f%%, ", 100 * (Optimum - LowerBound) / Optimum);
    printf("Ascent time = %0.0f sec.\n", GetTime() - LastTime);
    fflush(stdout);
    if (Norm == 0)
        return;
    GenerateCandidates(MaxCandidates, fabs(Excess * Cost),
                       CandidateSetSymmetric);
    if (CandidateFileName
        && (CandidateFile = fopen(CandidateFileName, "w"))) {
        Na = FirstNode;
        do {
            fprintf(CandidateFile, "%ld %ld", Na->Id,
                    Na->Dad ? Na->Dad->Id : 0);
            Count = 0;
            for (NNa = Na->CandidateSet; NNa->To; NNa++)
                Count++;
            fprintf(CandidateFile, " %d ", Count);
            for (NNa = Na->CandidateSet; NNa->To; NNa++)
                fprintf(CandidateFile, " %ld %ld", (NNa->To)->Id,
                        NNa->Alpha);
            fprintf(CandidateFile, "\n");
        } while ((Na = Na->Suc) != FirstNode);
        fprintf(CandidateFile, "-1\nEOF\n");
        fclose(CandidateFile);
    }

  End_CreateCandidateSet:
    if (C == C_EXPLICIT) {
        Na = FirstNode;
        do {
            Nb = Na;
            while ((Nb = Nb->Suc) != FirstNode) {
                if (Na->Id > Nb->Id)
                    Na->C[Nb->Id] += Na->Pi + Nb->Pi;
                else
                    Nb->C[Na->Id] += Na->Pi + Nb->Pi;
            }
        }
        while ((Na = Na->Suc) != FirstNode);
    }
    /* Read tours to be merged */
    for (i = 0; i <= 1; i++) {
        if (FirstNode->MergeSuc[i]) {
            Na = FirstNode;
            do {
                Nb = Na->MergeSuc[i];
                Count = 0;
                for (NNa = Na->CandidateSet; NNa->To && NNa->To != Nb;
                     NNa++)
                    Count++;
                if (!NNa->To) {
                    NNa->Cost = C(Na, Nb);
                    NNa->To = Nb;
                    NNa->Alpha = 0;
                    assert(Na->CandidateSet =
                           (Candidate *) realloc(Na->CandidateSet,
                                                 (Count +
                                                  2) * sizeof(Candidate)));
                    Na->CandidateSet[Count + 1].To = 0;
                }
                Count = 0;
                for (NNb = Nb->CandidateSet; NNb->To && NNb->To != Na;
                     NNb++)
                    Count++;
                if (!NNb->To) {
                    NNb->Cost = C(Na, Nb);
                    NNb->To = Na;
                    NNb->Alpha = 0;
                    assert(Nb->CandidateSet =
                           (Candidate *) realloc(Nb->CandidateSet,
                                                 (Count +
                                                  2) * sizeof(Candidate)));
                    Nb->CandidateSet[Count + 1].To = 0;
                }
            } while ((Na = Nb) != FirstNode);
        }
    }
}
