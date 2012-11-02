#ifndef _LK_H
#define _LK_H

/*
   This header is used by almost all functions of the program. It defines macros and  
   specifies data structures and function prototypes.
*/

#include <assert.h>
#include <ctype.h>
#include <limits.h>
#include <math.h>
#include <stdlib.h>
#include <stdio.h>
#include <string.h>

#include "Hashing.h"

/* Macro definitions */

#define Fixed(a,b) ((a)->FixedTo1 == (b) || (a)->FixedTo2 == (b))
#define Follow(b,a)\
        ((a)->Suc != (b) ?\
        Link((b)->Pred,(b)->Suc), Link(b,(a)->Suc), Link(a,b) : 0) 
#define InBestTour(a,b) ((a)->BestSuc == (b) || (b)->BestSuc == (a))
#define InNextBestTour(a,b) ((a)->NextBestSuc == (b) || (b)->NextBestSuc == (a))
#define Link(a,b) ((a)->Suc = (b), (b)->Pred = (a))
#define Near(a,b) ((a)->BestSuc ? InBestTour(a,b) : (a)->Dad == (b) || (b)->Dad == (a))
#define InOptimumTour(a,b) ((a)->OptimumSuc == (b) || (b)->OptimumSuc == (a))
#define IsCommonEdge(a,b) (((a)->MergeSuc[0] == (b) || (b)->MergeSuc[0] == (a)) &&\
                           ((a)->MergeSuc[1] == (b) || (b)->MergeSuc[1] == (a)))
#define Precede(a,b)\
        ((b)->Pred != (a) ?\
         Link((a)->Pred,(a)->Suc), Link((b)->Pred,a), Link(a,b) : 0)

enum Types {TSP, ATSP, SOP, HCP, CVRP, TOUR, HPP};
enum EdgeWeightTypes {EXPLICIT, EUC_2D, EUC_3D, MAX_2D, MAX_3D, MAN_2D, MAN_3D,
                      CEIL_2D, CEIL_3D, GEO, GEOM, ATT, XRAY1, XRAY2, SPECIAL};
enum EdgeWeightFormats {FUNCTION, FULL_MATRIX, UPPER_ROW, LOWER_ROW,
                        UPPER_DIAG_ROW, LOWER_DIAG_ROW, UPPER_COL, LOWER_COL, 			        
                        UPPER_DIAG_COL, LOWER_DIAG_COL};
enum CoordTypes {TWOD_COORDS, THREED_COORDS, NO_COORDS};

struct Candidate;
struct Segment;

/* The Node structure is used to represent nodes (cities) of the problem */

typedef struct Node {
    long Id;        /* The number of the node (1...Dimension) */ 
    long Loc;       /* The location of the node in the heap 
                       (zero, if the node is not in the heap) */ 
    long Rank;      /* During the ascent, the priority of the node.
                       Otherwise, the ordinal number of the node in the tour */
    long V;         /* During the ascent the degree of the node minus 2.
                       Otherwise, the variable is used to mark nodes */ 			   
    long LastV;     /* The last value of V during the ascent */
    long Cost;      /* The "best" cost of an edge emanating from the node */
    long NextCost;  /* During the ascent, the "next best" cost of an edge
                       emanating from the node. When the candidate set is
                       determined it denotes the associated beta-value */ 
    long Pi;        /* The pi-value of the node */
    long BestPi;    /* The currently best pi-value found during the ascent */
    long *C;        /* A row in the cost matrix */
    struct Node *Pred, *Suc; /* The predecessor and successor node in the two-way list 
                                of nodes */
    struct Node *OldPred, 	
                *OldSuc;     /* Previous values of Pred and Suc */  	
    struct Node *BestSuc, 
                *NextBestSuc;/* The best and next best successor node in the
                                currently best tour */
    struct Node *Dad;        /* The father of the node in the minimum 1-tree */
    struct Node *Next;       /* An auxiliary pointer, usually to the next node in
                                a list of nodes (e.g., the list of "active" nodes) */
    struct Node *FixedTo1,	
                *FixedTo2;   /* Pointers to the opposite end nodes of fixed edges.
                                A maximum of two fixed edges can be incident to a node */
    struct Node *OptimumSuc; /* The successor node as given in the TOUR_SECTION */
    struct Node *InitialSuc; /* The successor node as given in the INITIAL_TOUR file */
    struct Node *MergeSuc[2];/* The successor nodes as given in the MERGE_TOUR files */     
    struct Candidate *CandidateSet; /* The candidate array associated with the node */
    struct Segment *Parent;  /* The parent segment of a node when the two-level tree
                                representation is used */ 
    double X, Y, Z;          /* Coordinates of the node */
    int OldPredExcluded, 
        OldSucExcluded;      /* Booleans used for indicating that one (or both) of 
                                the adjoining edges on the tour has been excluded */	
} Node;

/* The Candidate structure is used to represent candidate edges */

typedef struct Candidate {
    Node *To;           /* A pointer to the end node of the edge */
    long Cost;          /* The cost (distance) of the edge */
    long Alpha;         /* Its alpha-value */
} Candidate; 

/* The Segment strucure is used to represent the segments in the two-level representation
   of tours */
            
typedef struct Segment {
    int Reversed;               /* The reversal bit */
    Node *First, *Last;         /* The first and last node in the segment */
    struct Segment *Pred, *Suc; /* The predecessor and successor in the two-way list of
                                   segments */ 
    long Rank;                  /* The ordinal number of the segment in the list */						
    long Size;                  /* The number of nodes in the segment */
} Segment;

/* The SwapRecord structure is used to record 2-opt moves (swaps) */ 
	
typedef struct SwapRecord {
    Node *t1, *t2, *t3, *t4;    /* The 4 nodes involved in a 2-opt move */
} SwapRecord;

/* Extern variables: */

extern long *BestTour;          /* A table containing best tour found */ 
extern long Dimension;          /* The number of nodes in the problem */
extern long MaxCandidates;      /* The maximum number of candidate edges to be 
                                   associated with each node */
extern long AscentCandidates;   /* The number of candidate edges to be associated 
                                   with each node during the ascent */
extern long InitialPeriod;      /* The length of the first period in the ascent */
extern long InitialStepSize;    /* The initial step size used in the ascent */
extern long Precision;          /* The internal precision in the representation of 
                                   transformed distances */
extern int RestrictedSearch;    /* Specifies whether the choice of the first edge
                                   to be broken is restricted */
extern long Runs;               /* The total number of runs */
extern long MaxTrials;          /* The maximum number of trials in each run */
extern long MaxSwaps;           /* The maximum number of swaps made during the search 
                                   for a move */
extern double BestCost;         /* The cost of the tour in BestTour */
extern double Excess;           /* The maximum alpha-value allowed for any candidate 
                                   edge is set to Excess times the absolute value of 
                                   the lower bound of a solution tour */
extern double Optimum;          /* Known optimal tour length. A run will be terminated 
                                   as soon as a tour length less than or equal to 
                                   optimum is achieved */
extern unsigned int Seed;       /* The initial seed for random number generation */
extern int Subgradient;         /* Specifies whether the pi-values should be determined 
                                   by subgradient optimization */
extern int MoveType;            /* Specifies the move type to be used in the local search.  
                                   The value r (= 2, 3, 4 or 5) signifies that a r-opt 
                                   move is to be used. */                                    
extern int BacktrackMoveType;   /* Specifies the backtrack move type to be used in the 
                                   local search.  The value r (= 2, 3, 4 or 5) signifies 
                                   that a r-opt move with backtracking is to be used.
                                   The value 0 signifies that no backtracking is 
                                   to be used. */
extern int TraceLevel;          /* Specifies the level of detail of the output given 
                                   during the solution process. The value 0 signifies 
                                   a minimum amount of output. The higher the value is 
                                   the more information is given */

extern Node *NodeSet;           /* Array of all nodes */
extern Node *FirstNode;         /* The first node in the list of nodes */			
extern Node *FirstActive, 
            *LastActive;        /* The first and last node in the list of "active" nodes */
extern Node **Heap;             /* The heap used for computing minimum spanning trees */
extern SwapRecord *SwapStack;   /* The stack of SwapRecords */
extern long Swaps;              /* The number of swaps made during a tentative move */
extern long Norm;               /* A measure of a 1-tree's discrepancy from a tour */
extern long M;                  /* The M-value used when solving an ATSP-problem by
                                   transforming it to a TSP-problem */
extern long GroupSize;          /* The desired initial size of each segment */
extern long Groups;             /* The current number of segments */
extern long Trial;              /* The ordinal number of the current trial */			  	
extern long *BetterTour;        /* A table containing the currently best tour in a run */
extern long *CacheVal;          /* A table of cached distances */		
extern long *CacheSig;          /* A table of the signatures of the cached distances */
extern long *CostMatrix;        /* The cost matrix */
extern double BetterCost;       /* The cost of the tour stored in BetterTour */
extern double LowerBound;       /* The lower bound found by the ascent */
extern unsigned long Hash;      /* The hash value corresponding to the current tour */
extern int *Rand;               /* A table of random values */
extern int Reversed;            /* A boolean used to indicate whether a tour has been
                                   reversed */
extern Segment *FirstSegment;   /* A pointer to the first segment in the cyclic list of 
                                   segments */
extern HashTable *HTable;       /* The hash table used for storing tours */

/* The following variables are read by the functions ReadParameters and ReadProblem: */		

extern FILE *ParameterFile, *ProblemFile, *PiFile, *TourFile, 
            *InputTourFile, *CandidateFile, *InitialTourFile,
            *MergeTourFile[2];
extern char *ParameterFileName, *ProblemFileName, *PiFileName, *TourFileName, 
            *InputTourFileName, *CandidateFileName, *InitialTourFileName,
            *MergeTourFileName[2];
extern char *Name, *Type, *EdgeWeightType, *EdgeWeightFormat, 
            *EdgeDataFormat, *NodeCoordType, *DisplayDataType;
extern int ProblemType, WeightType, WeightFormat, CoordType, CandidateSetSymmetric;

/* Function prototypes: */

extern long (*Distance) (Node *Na, Node *Nb);
long Distance_1(Node *Na, Node *Nb);
long Distance_ATSP(Node *Na, Node *Nb);
long Distance_ATT(Node *Na, Node *Nb);
long Distance_CEIL_2D(Node *Na, Node *Nb);
long Distance_CEIL_3D(Node *Na, Node *Nb);
long Distance_EXPLICIT(Node *Na, Node *Nb);
long Distance_EUC_2D(Node *Na, Node *Nb);
long Distance_EUC_3D(Node *Na, Node *Nb);
long Distance_GEO(Node *Na, Node *Nb);
long Distance_GEOM(Node *Na, Node *Nb);
long Distance_MAN_2D(Node *Na, Node *Nb);
long Distance_MAN_3D(Node *Na, Node *Nb);
long Distance_MAX_2D(Node *Na, Node *Nb);
long Distance_MAX_3D(Node *Na, Node *Nb);
long Distance_XRAY1(Node *Na, Node *Nb);
long Distance_XRAY2(Node *Na, Node *Nb);

extern long (*C) (Node *Na, Node *Nb);
long C_EXPLICIT(Node *Na, Node *Nb);
long C_FUNCTION(Node *Na, Node *Nb);

extern long (*D) (Node *Na, Node *Nb);
long D_EXPLICIT(Node *Na, Node *Nb);
long D_FUNCTION(Node *Na, Node *Nb);

extern long (*c) (Node *Na, Node *Nb);
long c_CEIL_2D(Node *Na, Node *Nb);
long c_CEIL_3D(Node *Na, Node *Nb);
long c_EUC_2D(Node *Na, Node *Nb);
long c_EUC_3D(Node *Na, Node *Nb);
long c_GEO(Node *Na, Node *Nb);
long c_GEOM(Node *Na, Node *Nb);

extern Node* (*BestMove) (Node *t1, Node *t2, long *G0, long *Gain);
Node *Best2OptMove(Node *t1, Node *t2, long *G0, long *Gain);
Node *Best3OptMove(Node *t1, Node *t2, long *G0, long *Gain);
Node *Best4OptMove(Node *t1, Node *t2, long *G0, long *Gain);
Node *Best5OptMove(Node *t1, Node *t2, long *G0, long *Gain);

extern Node* (*BacktrackMove) (Node *t1, Node *t2, long *G0, long *Gain);
Node *Backtrack2OptMove(Node *t1, Node *t2, long *G0, long *Gain);
Node *Backtrack3OptMove(Node *t1, Node *t2, long *G0, long *Gain);
Node *Backtrack4OptMove(Node *t1, Node *t2, long *G0, long *Gain);
Node *Backtrack5OptMove(Node *t1, Node *t2, long *G0, long *Gain);

void Activate(Node *t);
void AdjustCandidateSet();
double Ascent();
int Between(const Node *t2, const Node *t1, const Node *t3);
int Between_SL(const Node *t2, const Node *t1, const Node *t3);
long BridgeGain(Node *s1, Node *s2, Node *s3, Node *s4, 
                Node *s5, Node *s6, Node *s7, Node *s8, 
                int Case6, long G);
void ChooseInitialTour();
void Connect(Node * N1, const long Max, const int Sparse);
void CreateCandidateSet();
void eprintf(char *fmt, ...);
int Excludable(const Node *Na, const Node *Nb);
void Exclude(Node *Na, Node *Nb);
double FindTour(); 
void Flip(Node *t1, Node *t2, Node *t3);
void Flip_SL(Node *t1, Node *t2, Node *t3);
int Forbidden(const Node * ta, const Node * tb);
void FreeStructures();
long Gain23();
void GenerateCandidates(const long MaxCandidates, const long MaxAlpha, const int Symmetric);
double GetTime();
double LinKernighan();
void Make2OptMove(Node *t1, Node *t2, Node *t3, Node *t4);
void Make3OptMove(Node *t1, Node *t2, Node *t3, Node *t4, 
                  Node *t5, Node *t6, int Case);
void Make4OptMove(Node *t1, Node *t2, Node *t3, Node *t4, 
                  Node *t5, Node *t6, Node *t7, Node *t8, 
                  int Case);
void Make5OptMove(Node *t1, Node *t2, Node *t3, Node *t4, 
                  Node *t5, Node *t6, Node *t7, Node *t8, 
                  Node *t9, Node *t10, int Case);
double Minimum1TreeCost(const int Sparse);
void MinimumSpanningTree(const int Sparse);
void NormalizeNodeList();
void PrintBestTour();
void PrintParameters();
void ReadTour(char *FileName, FILE **File);
char *ReadLine(FILE *InputFile);
void ReadParameters();
void ReadProblem();
void RecordBestTour();
void RecordBetterTour();
Node *RemoveFirstActive();
void ResetCandidateSet();
void RestoreTour();
void StoreTour();

#endif

