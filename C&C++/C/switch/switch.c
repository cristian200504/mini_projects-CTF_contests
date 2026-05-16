#include <stdio.h>

int main(void) {
    int n;

    printf("Enter a number (-1, 0, or 1): ");
    scanf("%d", &n);

    switch (n) {
        case -1:
            printf("Negative\n");
            break;

        case 0:
            printf("Zero\n");
            break;

        case 1:
            printf("Positive\n");
            break;

        default:
            printf("Unhandled number: %d\n", n);
            break;
    }

    return 0;
}

