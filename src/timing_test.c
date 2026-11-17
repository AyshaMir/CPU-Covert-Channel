#include <stdio.h>
#include <time.h>
#define SAMPLES 20
#define ITERATIONS 1000000
int main() {
    double total = 0;
    for (int sample = 0; sample < SAMPLES; sample++) {
        struct timespec start, end;
        volatile unsigned long sum = 0;
        clock_gettime(CLOCK_MONOTONIC, &start);
        for (unsigned long i = 0; i < ITERATIONS; i++) {
            sum += i;
        }
        clock_gettime(CLOCK_MONOTONIC, &end);
        double elapsed = (end.tv_sec - start.tv_sec)+ (end.tv_nsec - start.tv_nsec) / 1e9;
        double elapsed_ms = elapsed * 1000;
        total += elapsed_ms;
        printf("Sample %d: %.6f ms\n",sample + 1, elapsed_ms);
    }
    printf("\nAverage execution time: %.6f ms\n", total / SAMPLES);
    return 0;
}