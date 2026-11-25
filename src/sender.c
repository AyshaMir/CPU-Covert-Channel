
#define _POSIX_C_SOURCE 200809L

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <errno.h>
#include <limits.h>
#include "protocol.h"

// Store timing information for each transmitted bit
typedef struct {
    char bit;
    long long scheduled_start_ns;
    long long scheduled_end_ns;
    long long actual_start_ns;
    long long actual_end_ns;
} TimingRecord;

// Convert a timespec timestamp to nanoseconds
static long long to_ns(struct timespec t) {
    return (long long)t.tv_sec * 1000000000LL + t.tv_nsec;
}

// Read the current monotonic time
static long long now_ns(void) {
    struct timespec t;

    if (clock_gettime(CLOCK_MONOTONIC, &t) != 0) {
        perror("clock_gettime failed");
        exit(EXIT_FAILURE);
    }

    return to_ns(t);
}

// Keep the CPU busy until an absolute deadline
static void cpu_busy_until(long long deadline_ns) {
    volatile unsigned long counter = 0;

    while (now_ns() < deadline_ns) {
        counter++;
    }
}

// Sleep until an absolute deadline
static void cpu_idle_until(long long deadline_ns) {
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

    if (result != 0) {
        fprintf(stderr,
                "clock_nanosleep failed: %s\n",
                strerror(result));
        exit(EXIT_FAILURE);
    }
}

int main(int argc, char *argv[]) {

    // Require message, duration, and start time
    if (argc != 4 && argc != 5) {
        fprintf(stderr,
                "Usage: %s <bits> <duration_ms> "
                "<start_ns> [--timing]\n",
                argv[0]);
        return 1;
    }

    // Check optional timing flag
    int timing_enabled = 0;

    if (argc == 5) {
        if (strcmp(argv[4], "--timing") != 0) {
            fprintf(stderr, "Unknown option: %s\n", argv[4]);
            return 1;
        }

        timing_enabled = 1;
    }

    const char *message = argv[1];

    // Parse bit duration
    char *end;
    errno = 0;

    long duration = strtol(argv[2], &end, 10);

    if (errno != 0 ||
        end == argv[2] ||
        *end != '\0' ||
        (duration != 50 &&
         duration != 100 &&
         duration != 200)) {

        fprintf(stderr,
                "Duration must be 50, 100, or 200 ms.\n");
        return 1;
    }

    // Validate message length
    size_t length = strlen(message);

    if (length == 0 || length > MAX_MESSAGE_BITS) {
        fprintf(stderr, "Invalid message length.\n");
        return 1;
    }

    // Validate binary message
    for (size_t i = 0; i < length; i++) {
        if (message[i] != '0' && message[i] != '1') {
            fprintf(stderr,
                    "Message must contain only 0 and 1.\n");
            return 1;
        }
    }

    // Parse shared start timestamp
    char *start_end;
    errno = 0;

    long long start_ns = strtoll(
        argv[3],
        &start_end,
        10
    );

    if (errno != 0 ||
        start_end == argv[3] ||
        *start_end != '\0' ||
        start_ns <= now_ns()) {

        fprintf(stderr,
                "Start time must be a valid future timestamp.\n");
        return 1;
    }

    // Set up fixed timing slots
    long long slot_ns =
        (long long)duration * 1000000LL;

    size_t preamble_length = strlen(PREAMBLE);
    size_t total_length = preamble_length + length;

    // Prevent timestamp overflow when calculating deadlines
    if (start_ns > LLONG_MAX -
        (long long)total_length * slot_ns) {

        fprintf(stderr,
                "Transmission deadline would overflow.\n");
        return 1;
    }

    printf("Preamble: %s\n", PREAMBLE);
    printf("Transmitting: %s\n", message);
    printf("Bit duration: %ld ms\n", duration);
    printf("Scheduled start: %lld ns\n", start_ns);

    // Allocate timing records only when requested
    TimingRecord *records = NULL;

    if (timing_enabled) {
        records = calloc(
            total_length,
            sizeof(TimingRecord)
        );

        if (records == NULL) {
            fprintf(stderr,
                    "Failed to allocate timing records.\n");
            return 1;
        }
    }

    // Wait until the agreed start time
    cpu_idle_until(start_ns);

    // Transmit preamble followed by message
    for (size_t i = 0; i < total_length; i++) {

        char bit = (i < preamble_length)
            ? PREAMBLE[i]
            : message[i - preamble_length];

        long long scheduled_start =
            start_ns + (long long)i * slot_ns;

        long long deadline_ns =
            start_ns + (long long)(i + 1) * slot_ns;

        // Record actual start time if timing is enabled
        if (timing_enabled) {
            records[i].bit = bit;
            records[i].scheduled_start_ns =
                scheduled_start;
            records[i].scheduled_end_ns =
                deadline_ns;
            records[i].actual_start_ns = now_ns();
        }

        // Transmit bit using CPU activity
        if (bit == '1') {
            cpu_busy_until(deadline_ns);
        } else {
            cpu_idle_until(deadline_ns);
        }

        // Record actual end time
        if (timing_enabled) {
            records[i].actual_end_ns = now_ns();
        }
    }

    // Print timing measurements after transmission
    if (timing_enabled) {

        printf("\nTIMING_RESULTS_BEGIN\n");

        printf(
            "slot,bit,scheduled_start_ns,scheduled_end_ns,"
            "actual_start_ns,actual_end_ns,"
            "start_error_ms,end_error_ms\n"
        );

        for (size_t i = 0; i < total_length; i++) {

            double start_error =
                (records[i].actual_start_ns -
                 records[i].scheduled_start_ns) / 1000000.0;

            double end_error =
                (records[i].actual_end_ns -
                 records[i].scheduled_end_ns) / 1000000.0;

            printf(
                "%zu,%c,%lld,%lld,%lld,%lld,%.6f,%.6f\n",
                i + 1,
                records[i].bit,
                records[i].scheduled_start_ns,
                records[i].scheduled_end_ns,
                records[i].actual_start_ns,
                records[i].actual_end_ns,
                start_error,
                end_error
            );
        }

        printf("TIMING_RESULTS_END\n");

        free(records);
    }

    printf("Transmission complete!\n");

    return 0;
}
