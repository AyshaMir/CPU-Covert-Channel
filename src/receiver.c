#define _POSIX_C_SOURCE 200809L

#include <stdio.h>
#include <stdlib.h>
#include <time.h>
#include <math.h>
#include "protocol.h"

double measure_execution_time(void) {

    struct timespec start, end;
    volatile unsigned long sum = 0;

    clock_gettime(CLOCK_MONOTONIC, &start);

    for (unsigned long i = 0; i < 1000000; i++) {
        sum += i;
    }

    clock_gettime(CLOCK_MONOTONIC, &end);

    double elapsed = (end.tv_sec - start.tv_sec)
                   + (end.tv_nsec - start.tv_nsec) / 1e9;

    return elapsed * 1000;
}

int main(int argc, char *argv[]) {

    int samples = 100;

    if (argc > 1) {
        samples = atoi(argv[1]);
    }

    if (samples <= 0 || samples > 100000) {
        fprintf(stderr, "Invalid sample count.\n");
        return 1;
    }

    double *timings = malloc(samples * sizeof(double));

    if (timings == NULL) {
        fprintf(stderr, "Memory allocation failed.\n");
        return 1;
    }

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
    printf("sample,execution_time_ms\n");
    for (int i = 0; i < samples; i++) {
        printf("%d,%.6f\n", i + 1, timings[i]);
    }
    fprintf(stderr, "\nSamples: %d\n", samples);
    fprintf(stderr, "Average: %.6f ms\n", average);
    fprintf(stderr, "Minimum: %.6f ms\n", min);
    fprintf(stderr, "Maximum: %.6f ms\n", max);
    fprintf(stderr, "Standard deviation: %.6f ms\n", std_dev);
    free(timings);
    return 0;
}