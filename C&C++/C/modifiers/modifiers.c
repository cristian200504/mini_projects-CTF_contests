#include <stdio.h>
#include <limits.h>   // for INT_MAX, etc.

int main(void) {
    signed int s = -10;
    unsigned int u = 10U;
    short sh = 32767;           // max for 16-bit short
    long l = 1000000L;
    const int c = 5;            // cannot change
    volatile int v = 42;        // value may change externally

    printf("signed int s = %d\n", s);
    printf("unsigned int u = %u\n", u);
    printf("short sh = %hd\n", sh);
    printf("long l = %ld\n", l);
    printf("const int c = %d\n", c);
    printf("volatile int v = %d\n", v);

    printf("\nINT_MAX = %d\n", INT_MAX);
    printf("INT_MIN = %d\n", INT_MIN);
    printf("UINT_MAX = %u\n", UINT_MAX);

    return 0;
}

