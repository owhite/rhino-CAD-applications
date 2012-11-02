#include "LK.h"
#include "Heap.h"

/*
   A binary heap is used to implement a priority queue. 

   A heap is useful in order to speed up the computations of minimum 
   spanning trees. The elements of the heap are the nodes, and the
   priorities (ranks) are their associated costs (their minimum distance 
   to the current tree). 
*/

static long HeapCount;          /* Its current number of elements */

/*      
   MakeHeap creates an empty heap. 
*/

void MakeHeap(const long Size)
{
    assert(Heap = (Node **) malloc((Size + 1) * sizeof(Node *)));
    HeapCount = 0;
}

/*
   The SiftUp function is called when the rank of a node is decreased.
   The function moves the node forward in the heap (the foremost node
   of the heap has the lowest rank).

   When calling SiftUp(N), node N must belong to the heap.              
*/

void SiftUp(Node * N)
{
    long Loc = N->Loc, P = Loc / 2;

    while (P && N->Rank < Heap[P]->Rank) {
        Heap[Loc] = Heap[P];
        Heap[Loc]->Loc = Loc;
        Loc = P;
        P /= 2;
    }
    Heap[Loc] = N;
    Heap[Loc]->Loc = Loc;
}

/*       
   The DeleteMin function deletes the foremost node from the heap. 
   The function returns a pointer to the deleted node (0, if the heap
   is empty).
*/

Node *DeleteMin()
{
    Node *Remove, *Item;
    long Ch, Loc;

    if (!HeapCount)
        return 0;
    Remove = Heap[1];
    Item = Heap[HeapCount];
    HeapCount--;
    Loc = 1;
    Ch = 2 * Loc;

    while (Ch <= HeapCount) {
        if (Ch < HeapCount && Heap[Ch + 1]->Rank < Heap[Ch]->Rank)
            Ch++;
        if (Heap[Ch]->Rank >= Item->Rank)
            break;
        Heap[Loc] = Heap[Ch];
        Heap[Loc]->Loc = Loc;
        Loc = Ch;
        Ch *= 2;
    }
    Heap[Loc] = Item;
    Item->Loc = Loc;
    Remove->Loc = 0;
    return Remove;
}

/*       
   The Insert function insert a node into the heap.
   When calling Insert(N), node N must belong to the heap.
*/

void Insert(Node * N)
{
    long Ch, P;

    Ch = ++HeapCount;
    P = Ch / 2;
    while (P && N->Rank < Heap[P]->Rank) {
        Heap[Ch] = Heap[P];
        Heap[Ch]->Loc = Ch;
        Ch = P;
        P /= 2;
    }
    Heap[Ch] = N;
    N->Loc = Ch;
}
