#include "LK.h"

/* 
   Functions for computing the transformed distance of an edge (Na,Nb). 
*/

/* 
   The C_EXPLICIT function returns the distance by looking it up in a table. 
*/


long C_EXPLICIT(Node * Na, Node * Nb)
{
    return Na->Id < Nb->Id ? Nb->C[Na->Id] : Na->C[Nb->Id];
}

/*
   The C_FUNCTION function is used when the distance is defined by a
   function (e.g. the Euclidean distance function). In order to speed
   up the computations the following algorithm used:
	
   (1) If the edge (Na,Nb) is a candidate edge incident to Na, then
       its distance is available in the field Cost of the corresponding
       Candidate structure.
	    
   (2) A hash table (CacheVal) is consulted to see if the distance has
       been stored. 
	    
   (3) Otherwise the distance function is called and the distance computed
       is stored in the hash table.
	    
   [ see Bentley (1990): K-d trees for semidynamic point sets. ] 
	      
*/

long C_FUNCTION(Node * Na, Node * Nb)
{
    Node *Nc;
    Candidate *Cand;
    long Index, i, j;

    if (Cand = Na->CandidateSet)
        for (; Nc = Cand->To; Cand++)
            if (Nc == Nb)
                return Cand->Cost;
    if (CacheSig == 0)
        return D(Na, Nb);
    i = Na->Id;
    j = Nb->Id;
    Index = i ^ j;
    if (i > j)
        i = j;
    if (CacheSig[Index] == i)
        return CacheVal[Index];
    CacheSig[Index] = i;
    return (CacheVal[Index] = D(Na, Nb));
}

long D_EXPLICIT(Node * Na, Node * Nb)
{
    return (Na->Id <
            Nb->Id ? Nb->C[Na->Id] : Na->C[Nb->Id]) + Na->Pi + Nb->Pi;
}

long D_FUNCTION(Node * Na, Node * Nb)
{
    return (Fixed(Na, Nb) ? 0 : Distance(Na, Nb) * Precision) + Na->Pi +
        Nb->Pi;
}

/* Functions for computing lower bounds for the distance functions */

long c_CEIL_2D(Node * Na, Node * Nb)
{
    long dx = ceil(fabs(Na->X - Nb->X)), dy = ceil(fabs(Na->Y - Nb->Y));
    return (dx > dy ? dx : dy) * Precision + Na->Pi + Nb->Pi;
}

long c_CEIL_3D(Node * Na, Node * Nb)
{
    long dx = ceil(fabs(Na->X - Nb->X)),
        dy = ceil(fabs(Na->Y - Nb->Y)), dz = ceil(fabs(Na->Z - Nb->Z));
    if (dy > dx)
        dx = dy;
    if (dz > dx)
        dx = dz;
    return dx * Precision + Na->Pi + Nb->Pi;
}

long c_EUC_2D(Node * Na, Node * Nb)
{
    long dx = fabs(Na->X - Nb->X) + 0.5, dy = fabs(Na->Y - Nb->Y) + 0.5;
    return (dx > dy ? dx : dy) * Precision + Na->Pi + Nb->Pi;
}

long c_EUC_3D(Node * Na, Node * Nb)
{
    long dx = fabs(Na->X - Nb->X) + 0.5,
        dy = fabs(Na->Y - Nb->Y) + 0.5, dz = fabs(Na->Z - Nb->Z) + 0.5;
    if (dy > dx)
        dx = dy;
    if (dz > dx)
        dx = dz;
    return dx * Precision + Na->Pi + Nb->Pi;
}

#define PI 3.141592
#define RRR 6378.388

long c_GEO(Node * Na, Node * Nb)
{
    long da = Na->X, db = Nb->X;
    double ma = Na->X - da, mb = Nb->X - db;
    long dx = RRR * PI / 180.0 * fabs(da - db + 5.0 * (ma - mb) / 3.0);
    return dx * Precision + Na->Pi + Nb->Pi;
}

#undef M_PI
#define M_PI 3.14159265358979323846264

long c_GEOM(Node * Na, Node * Nb)
{
    long dx = 6378388.0 * M_PI / 180.0 * fabs(Na->X - Nb->X) + 1.0;
    return dx * Precision + Na->Pi + Nb->Pi;
}
