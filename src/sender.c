
#define _POSIX_C_SOURCE 200809L

#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>
#include <errno.h>
#include "protocol.h"

// Convert a timespec timestamp to nanoseconds
static long long to_ns(struct timespec t) {
    return (long long)t.tv_sec * 1000000000LL + t.tv_nsec;
}

// Read the current monotonic time
static long long now_ns(void) {
    struct timespec t;
    clock_gettime(CLOCK_MONOTONIC, &t);
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
}

int main(int argc, char *argv[]) {

    // Require message, duration, and start time
    if (argc != 4) {
        fprintf(stderr,
                "Usage: %s <bits> <duration_ms> <start_ns>\n",
                argv[0]);
        return 1;
    }

    const char *message = argv[1];

    // Parse bit duration
    char *end;
    errno = 0;
    long duration = strtol(argv[2], &end, 10);

    if (errno != 0 || end == argv[2] || *end != '\0' ||
        (duration != 50 && duration != 100 && duration != 200)) {
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
    long long start_ns = strtoll(argv[3], &start_end, 10);

    if (errno != 0 || start_end == argv[3] ||
        *start_end != '\0' || start_ns <= now_ns()) {
        fprintf(stderr,
                "Start time must be a valid future timestamp.\n");
        return 1;
    }

    // Set up fixed timing slots
    long long slot_ns = (long long)duration * 1000000LL;

    size_t preamble_length = strlen(PREAMBLE);
    size_t total_length = preamble_length + length;

    printf("Preamble: %s\n", PREAMBLE);
    printf("Transmitting: %s\n", message);
    printf("Bit duration: %ld ms\n", duration);
    printf("Scheduled start: %lld ns\n", start_ns);

    // Wait until the agreed start time
    cpu_idle_until(start_ns);

    // Transmit preamble followed by message
    for (size_t i = 0; i < total_length; i++) {

        char bit = (i < preamble_length)
            ? PREAMBLE[i]
            : message[i - preamble_length];

        long long deadline_ns =
            start_ns + (i + 1) * slot_ns;

        if (bit == '1') {
            cpu_busy_until(deadline_ns);
        } else {
            cpu_idle_until(deadline_ns);
        }
    }

    printf("Transmission complete!\n");
    return 0;
}
