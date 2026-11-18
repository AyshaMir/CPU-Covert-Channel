#define _POSIX_C_SOURCE 200809L
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <errno.h>
#include <limits.h>
#include "protocol.h"

// Get current monotonic time in nanoseconds
static long long now_ns(void) {
    struct timespec t;
    clock_gettime(CLOCK_MONOTONIC, &t);

    return (long long)t.tv_sec * 1000000000LL
           + t.tv_nsec;
}

// Get CPU execution time in nanoseconds
static long long cpu_time_ns(void) {
    struct timespec t;
    clock_gettime(CLOCK_PROCESS_CPUTIME_ID, &t);

    return (long long)t.tv_sec * 1000000000LL
           + t.tv_nsec;
}

// Wait until an absolute timestamp
static void wait_until(long long deadline_ns) {
    struct timespec deadline = {
        .tv_sec = deadline_ns / 1000000000LL,
        .tv_nsec = deadline_ns % 1000000000LL
    };

    int result;

    do {
        result = clock_nanosleep(
            CLOCK_MONOTONIC,
            TIMER_ABSTIME,
            &deadline,
            NULL
        );
    } while (result == EINTR);
}

// Measure the proportion of time spent executing
static double measure_slot(long long deadline_ns) {

    volatile unsigned long counter = 0;

    long long wall_start = now_ns();
    long long cpu_start = cpu_time_ns();

    while (now_ns() < deadline_ns) {
        counter++;
    }

    long long cpu_end = cpu_time_ns();
    long long wall_end = now_ns();

    long long wall_elapsed = wall_end - wall_start;
    long long cpu_elapsed = cpu_end - cpu_start;

    if (wall_elapsed <= 0) {
        return -1;
    }

    return (double)cpu_elapsed / wall_elapsed;
}

// Decode measurements
static int decode(const double measurements[],
                  size_t message_length) {

    size_t preamble_length = strlen(PREAMBLE);
    size_t total_length = preamble_length + message_length;

    double busy_total = 0;
    double idle_total = 0;

    int busy_count = 0;
    int idle_count = 0;

    // Calculate reference values using the preamble
    for (size_t i = 0; i < preamble_length; i++) {

        if (PREAMBLE[i] == '1') {
            busy_total += measurements[i];
            busy_count++;
        } else {
            idle_total += measurements[i];
            idle_count++;
        }
    }

    if (busy_count == 0 || idle_count == 0) {
        fprintf(stderr, "Invalid preamble configuration.\n");
        return 1;
    }

    double busy_average = busy_total / busy_count;
    double idle_average = idle_total / idle_count;

    printf("Busy reference: %.6f\n", busy_average);
    printf("Idle reference: %.6f\n", idle_average);

    if (busy_average >= idle_average) {
        fprintf(stderr, "Unable to distinguish CPU activity.\n");
        return 1;
    }

    double threshold = (busy_average + idle_average) / 2.0;

    printf("Threshold: %.6f\n", threshold);

    char decoded[MAX_MESSAGE_BITS + sizeof(PREAMBLE)];

    // Interpret each measurement
    for (size_t i = 0; i < total_length; i++) {
        decoded[i] = measurements[i] < threshold ? '1' : '0';
    }

    decoded[total_length] = '\0';

    // Check the interpreted preamble
    if (strncmp(decoded, PREAMBLE, preamble_length) != 0) {
        fprintf(stderr, "Preamble validation failed.\n");
        return 1;
    }

    printf("Preamble: %s\n", PREAMBLE);
    printf("Received message: %s\n", decoded + preamble_length);

    return 0;
}

// Independently test decoding using synthetic data
static int self_test(void) {

    const double measurements[] = {
        0.48, 0.51, 0.49, 0.50,
        0.95, 0.97, 0.94, 0.96,
        0.49, 0.96, 0.50, 0.95,
        0.48, 0.97, 0.51, 0.94
    };

    printf("Running synthetic receiver test\n");

    return decode(measurements, 8);
}

int main(int argc, char *argv[]) {

    // Independent testing mode
    if (argc == 2 && strcmp(argv[1], "--self-test") == 0) {
        return self_test();
    }

    // Validate number of arguments
    if (argc != 4) {
        fprintf(stderr,
                "Usage: %s <message_length> <duration_ms> <start_ns>\n",
                argv[0]);

        return 1;
    }

    char *end;

    // Validate message length
    errno = 0;
    long message_length = strtol(argv[1], &end, 10);

    if (errno != 0 || end == argv[1] || *end != '\0' ||
        message_length <= 0 ||
        message_length > MAX_MESSAGE_BITS) {

        fprintf(stderr, "Invalid message length.\n");
        return 1;
    }

    // Validate bit duration
    errno = 0;
    long duration = strtol(argv[2], &end, 10);

    if (errno != 0 || end == argv[2] || *end != '\0' ||
        (duration != 50 && duration != 100 && duration != 200)) {

        fprintf(stderr, "Duration must be 50, 100, or 200 ms.\n");
        return 1;
    }

    // Validate start timestamp
    errno = 0;
    long long start_ns = strtoll(argv[3], &end, 10);

    if (errno != 0 || end == argv[3] || *end != '\0' ||
        start_ns <= now_ns()) {

        fprintf(stderr, "Invalid future start timestamp.\n");
        return 1;
    }

    long long slot_ns = duration * 1000000LL;

    size_t total_length = strlen(PREAMBLE) + message_length;

    if (start_ns > LLONG_MAX - (long long)total_length * slot_ns) {
        fprintf(stderr, "Timestamp overflow.\n");
        return 1;
    }

    double measurements[MAX_MESSAGE_BITS + sizeof(PREAMBLE)];

    printf("Expected message length: %ld bits\n", message_length);
    printf("Bit duration: %ld ms\n", duration);
    printf("Scheduled start: %lld ns\n", start_ns);

    fflush(stdout);

    wait_until(start_ns);

    // Collect measurements
    for (size_t i = 0; i < total_length; i++) {

        long long deadline_ns =
            start_ns + (long long)(i + 1) * slot_ns;

        if (now_ns() >= deadline_ns) {
            fprintf(stderr, "Missed measurement interval.\n");
            return 1;
        }

        measurements[i] = measure_slot(deadline_ns);

        if (measurements[i] < 0) {
            fprintf(stderr, "Measurement failed.\n");
            return 1;
        }
    }

    // Display collected measurements
    printf("\nSlot,CPU_time_ratio\n");

    for (size_t i = 0; i < total_length; i++) {
        printf("%zu,%.6f\n", i + 1, measurements[i]);
    }

    printf("\n");

    return decode(measurements, message_length);
}
