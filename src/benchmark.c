#define _POSIX_C_SOURCE 200809L

#include <math.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

#define BENCHMARK_ITERATIONS 1000000UL

static double measure_once_ms(void)
{
    struct timespec start, end;
    volatile unsigned long sum = 0;

    clock_gettime(CLOCK_MONOTONIC, &start);

    for (unsigned long i = 0; i < BENCHMARK_ITERATIONS; i++) {
        sum += i;
    }

    clock_gettime(CLOCK_MONOTONIC, &end);

    double elapsed = (double)(end.tv_sec - start.tv_sec)
                   + (double)(end.tv_nsec - start.tv_nsec) / 1e9;

    (void)sum;
    return elapsed * 1000.0;
}

static void usage(const char *prog)
{
    fprintf(stderr,
            "Usage: %s [samples] [--csv]\n"
            "  Legitimate-workload probe (1M integer adds). Default: 1 sample, human-readable stderr.\n"
            "  --csv: print sample,execution_time_ms header and rows on stdout.\n",
            prog);
}

int main(int argc, char *argv[])
{
    int samples = 1;
    int csv_mode = 0;

    for (int i = 1; i < argc; i++) {
        if (strcmp(argv[i], "--csv") == 0) {
            csv_mode = 1;
        } else if (strcmp(argv[i], "-h") == 0 || strcmp(argv[i], "--help") == 0) {
            usage(argv[0]);
            return 0;
        } else {
            char *end = NULL;
            long n = strtol(argv[i], &end, 10);
            if (end == argv[i] || *end != '\0' || n <= 0 || n > 100000) {
                usage(argv[0]);
                return 1;
            }
            samples = (int)n;
        }
    }

    double total = 0.0;
    double min = INFINITY;
    double max = 0.0;

    if (csv_mode) {
        printf("sample,execution_time_ms\n");
    }

    for (int i = 0; i < samples; i++) {
        double ms = measure_once_ms();
        total += ms;
        if (ms < min) {
            min = ms;
        }
        if (ms > max) {
            max = ms;
        }
        if (csv_mode) {
            printf("%d,%.6f\n", i + 1, ms);
        }
    }

    double avg = total / (double)samples;

    if (csv_mode) {
        fprintf(stderr,
                "samples=%d avg_ms=%.6f min_ms=%.6f max_ms=%.6f\n",
                samples, avg, min, max);
    } else {
        printf("%.6f\n", avg);
    }

    return 0;
}