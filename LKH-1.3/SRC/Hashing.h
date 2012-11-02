#ifndef _HASHING
#define _HASHING

/*
   This header specifies the interface for hashing.   
*/

#include <limits.h>
#include <float.h>

#define HashTableSize 65521    /* The largest prime less than INT_MAX */
#define MaxLoadFactor 0.75

typedef struct HashTableEntry {
    unsigned long Hash;
    double Cost;
} HashTableEntry;

typedef struct HashTable {
    HashTableEntry Entry[HashTableSize];
    long Count;                /* Number occupied entries in the table */
} HashTable;

void HashInitialize(HashTable * T);

void HashInsert(HashTable * T, unsigned long Hash, double Cost);

int HashSearch(HashTable * T, unsigned long Hash, double Cost);

#endif

