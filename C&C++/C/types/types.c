#include <stdio.h>

int main(void) {
    char c;
    int i;
    long l;
    float f;
    double d;

    printf("sizeof(char)   = %zu bytes\n", sizeof(c));
    printf("sizeof(int)    = %zu bytes\n", sizeof(i));
    printf("sizeof(long)   = %zu bytes\n", sizeof(l));
    printf("sizeof(float)  = %zu bytes\n", sizeof(f));
    printf("sizeof(double) = %zu bytes\n", sizeof(d));

    return 0;
}

