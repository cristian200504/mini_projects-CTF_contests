#include <stdio.h>

int make_sum(int a, int b) {
    int s = a + b;     // local lives only during this call
    return s;          // OK: returning a value (copied)
}

int* bad_sum_ptr(int a, int b) {
    int s = a + b;     // local stack variable
    return &s;         // ❌ BUG: returning address of a dead local
}

int* good_static_sum_ptr(int a, int b) {
    static int s;      // static storage lifetime (persists)
    s = a + b;
    return &s;         // ✅ OK: address remains valid
}

int main(void) {
    int v  = make_sum(2, 5);
    int *p = bad_sum_ptr(2, 5);        // UB: dangling pointer
    int *q = good_static_sum_ptr(2, 5);

    printf("make_sum: %d\n", v);
    printf("good_static_sum_ptr: %d\n", *q);
    printf("bad_sum_ptr (UB) : %d\n", *p) //may print garbage or crash
    return 0;
}

