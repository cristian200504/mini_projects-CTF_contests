#include <stdio.h>

int main(void) {
    int a = 10;
    int b = 3;
    int result;

    // Arithmetic
    result = a + b;
    printf("a + b = %d\n", result);

    result = a - b;
    printf("a - b = %d\n", result);

    result = a * b;
    printf("a * b = %d\n", result);

    result = a / b;
    printf("a / b = %d\n", result);

    result = a % b;
    printf("a %% b = %d\n", result); // %% prints a literal %

    // Assignment shorthands
    a += 2;   // same as a = a + 2;
    printf("a += 2 -> %d\n", a);

    a *= 3;   // same as a = a * 3;
    printf("a *= 3 -> %d\n", a);

    a -= 4;   // same as a = a - 4;
    printf("a -= 4 -> %d\n", a);

    return 0;
}

