#include <stdio.h>

int main(void) {
    printf("Using post-increment:\n");
    for (int i = 0; i < 5; i++) {
        printf("%d ", i);
    }

    printf("\n\nUsing pre-increment:\n");
    for (int i = 0; i < 5; ++i) {
        printf("%d ", i);
    }

    printf("\n");
    return 0;
}
