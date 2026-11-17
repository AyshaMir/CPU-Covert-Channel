#include <stdio.h>
#include <time.h>
#include "protocol.h"
#include <math.h>

double measure_execution_time() {
    struct timespec start, end;
    volatile unsigned long sum = 0;
    clock_gettime(CLOCK_MONOTONIC, &start);
    for (unsigned long i = 0; i < 1000000; i++) {
        sum += i;
    }
    clock_gettime(CLOCK_MONOTONIC, &end);
    double elapsed = (end.tv_sec - start.tv_sec)+ (end.tv_nsec - start.tv_nsec) / 1e9;
    return elapsed * 1000;
}

int main() {

    int samples = 100;

    double timings[100];
    double total = 0;
    double min = INFINITY;
    double max = 0;

    for (int i = 0; i < samples; i++) {

        timings[i] = measure_execution_time();

        total += timings[i];

        if (timings[i] < min)
            min = timings[i];

        if (timings[i] > max)
            max = timings[i];
    }

    double average = total / samples;
    double variance = 0;

    for (int i = 0; i < samples; i++) {
        variance += pow(timings[i] - average, 2);
    }

    variance /= samples;

    double std_dev = sqrt(variance);

    printf("Samples: %d\n", samples);
    printf("Average: %.6f ms\n", average);
    printf("Minimum: %.6f ms\n", min);
    printf("Maximum: %.6f ms\n", max);
    printf("Standard deviation: %.6f ms\n", std_dev);

    return 0;
}