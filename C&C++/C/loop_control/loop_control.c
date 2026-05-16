#include <stdio.h>

int main(void) {
    for (int i = 1; i <= 10; ++i) {

        if (i == 5) {
            printf("Skipping %d (continue)\n", i);
            continue;  // jump to next iteration, skip print below
        }

        if (i == 8) {
            printf("Breaking at %d (break)\n", i);
            break;     // exit the loop entirely
        }

        printf("Current i = %d\n", i);
    }

    printf("Loop finished.\n");
    return 0;
}

