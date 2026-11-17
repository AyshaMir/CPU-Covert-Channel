#include <stdio.h>
#include <time.h>

int main() {
    struct timespec start, end; //Creates two variables for storing timestamps.
    volatile unsigned long sum = 0;
    clock_gettime(CLOCK_MONOTONIC, &start);
    for (unsigned long i = 0; i < 1000000; i++) {
        sum += i;
    }
    clock_gettime(CLOCK_MONOTONIC, &end);
    double elapsed;
    elapsed = (end.tv_sec - start.tv_sec)
            + (end.tv_nsec - start.tv_nsec) / 1e9;
    printf("Execution time: %.6f seconds\n", elapsed);
    printf("Execution time: %.6f ms\n", elapsed * 1000);
    return 0;
}