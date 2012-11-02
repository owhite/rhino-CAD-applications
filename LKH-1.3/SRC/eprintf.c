#include "LK.h"
#include <stdarg.h>

/* 
   The eprintf function prints an error message and exits.
*/

void eprintf(char *fmt, ...)
{
    va_list args;

    fflush(stdout);
    va_start(args, fmt);
    vfprintf(stderr, fmt, args);
    va_end(args);
    fprintf(stderr, "\n");
    exit(2);
}
