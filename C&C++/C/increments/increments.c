#include <stdio.h>

int main(void) {
    int a = 5;

    printf("Initial a = %d\n", a);

    printf("Post-increment: a++ = %d\n", a++);   // use then increment
    printf("After post-increment, a = %d\n", a);

    printf("Pre-increment: ++a = %d\n", ++a);    // increment then use
    printf("After pre-increment, a = %d\n", a);

    printf("Post-decrement: a-- = %d\n", a--);   // use then decrement
    printf("After post-decrement, a = %d\n", a);

    printf("Pre-decrement: --a = %d\n", --a);    // decrement then use
    printf("After pre-decrement, a = %d\n", a);

    return 0;
}

