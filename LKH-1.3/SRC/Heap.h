#ifndef HEAP_H
#define HEAP_H

/* 
   This header specifies the interface for the use of heaps. 
*/

#include "LK.h"

void SiftUp(Node * N);
void MakeHeap(const long Size);
Node *DeleteMin();
void Insert(Node * N);

#endif

