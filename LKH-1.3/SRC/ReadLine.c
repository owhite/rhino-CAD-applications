#include "LK.h"

/*      
   The ReadLine function reads the next input line from a file. The function
   handles the problem that an input line may be terminated by a carriage
   return, a newline, both, or EOF.
*/

static char *Buffer = 0;
static unsigned long MaxBuffer = 0;

static int EndOfLine(FILE * InputFile, int c)
{
    int EOL = (c == '\r' || c == '\n');
    if (c == '\r') {
        c = fgetc(InputFile);
        if (c != '\n' && c != EOF)
            ungetc(c, InputFile);
    }
    return EOL;
}

char *ReadLine(FILE * InputFile)
{
    int i, c;

    if (Buffer == 0)
        assert(Buffer = (char *) malloc(MaxBuffer = 1));
    for (i = 0; (c = fgetc(InputFile)) != EOF && !EndOfLine(InputFile, c);
         i++) {
        if (i >= MaxBuffer - 1) {
            MaxBuffer *= 2;
            assert(Buffer = (char *) realloc(Buffer, MaxBuffer));
        }
        Buffer[i] = (char) c;
    }
    Buffer[i] = '\0';
    return c == EOF && i == 0 ? 0 : Buffer;
}
