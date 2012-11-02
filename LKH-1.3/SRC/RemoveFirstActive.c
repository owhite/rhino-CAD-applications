#include "LK.h"

/* 
   The RemoveFirstActive function removes the first node in the list 
   of "active" nodes (i.e., nodes to be tried as an anchor node, t1,
   by the LinKernighan algorithm).

   The function returns a pointer to the node removes. 

   The list must not be empty before the call. 
*/

Node *RemoveFirstActive()
{
    Node *t = FirstActive;
    if (FirstActive == LastActive)
        FirstActive = LastActive = 0;
    else
        FirstActive = FirstActive->Next;
    if (t)
        t->Next = 0;
    return t;
}
