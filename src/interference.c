#define _POSIX_C_SOURCE 200809L

#include <errno.h>
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/types.h>
#include <sys/wait.h>
#include <time.h>
#include <unistd.h>

static volatile sig_atomic_t keep_running = 1;

static void on_signal(int sig)
{
    (void)sig;
    keep_running = 0;
}

static long long now_ns(void)
{
    struct timespec t;
    clock_gettime(CLOCK_MONOTONIC, &t);
    return (long long)t.tv_sec * 1000000000LL + (long long)t.tv_nsec;
}

static void worker_loop(void)
{
    volatile unsigned long counter = 0;

    while (keep_running) {
        counter++;
        if ((counter & 0xFFFFUL) == 0UL) {
            if (!keep_running) {
                break;
            }
        }
    }
    _exit(0);
}

static void usage(const char *prog)
{
    fprintf(stderr,
            "Usage: %s <workers>\n"
            "  Spawn <workers> CPU-bound child processes until SIGINT/SIGTERM.\n",
            prog);
}

int main(int argc, char *argv[])
{
    if (argc != 2) {
        usage(argv[0]);
        return 1;
    }

    char *end = NULL;
    errno = 0;
    long workers = strtol(argv[1], &end, 10);
    if (errno != 0 || end == argv[1] || *end != '\0' || workers < 1 || workers > 256) {
        fprintf(stderr, "Workers must be an integer from 1 to 256.\n");
        return 1;
    }

    struct sigaction sa;
    memset(&sa, 0, sizeof(sa));
    sa.sa_handler = on_signal;
    sigemptyset(&sa.sa_mask);
    sigaction(SIGINT, &sa, NULL);
    sigaction(SIGTERM, &sa, NULL);

    pid_t *pids = calloc((size_t)workers, sizeof(pid_t));
    if (pids == NULL) {
        perror("calloc");
        return 1;
    }

    long long start = now_ns();
    fprintf(stderr, "interference: starting %ld worker(s), pid=%d\n", workers, (int)getpid());

    for (long i = 0; i < workers; i++) {
        pid_t pid = fork();
        if (pid < 0) {
            perror("fork");
            for (long j = 0; j < i; j++) {
                kill(pids[j], SIGTERM);
            }
            free(pids);
            return 1;
        }
        if (pid == 0) {
            free(pids);
            worker_loop();
        }
        pids[i] = pid;
    }

    while (keep_running) {
        pause();
    }

    fprintf(stderr, "interference: stopping workers...\n");
    for (long i = 0; i < workers; i++) {
        if (pids[i] > 0) {
            kill(pids[i], SIGTERM);
        }
    }

    for (long i = 0; i < workers; i++) {
        if (pids[i] > 0) {
            waitpid(pids[i], NULL, 0);
        }
    }

    long long elapsed_ms = (now_ns() - start) / 1000000LL;
    fprintf(stderr, "interference: ran ~%lld ms\n", elapsed_ms);

    free(pids);
    return 0;
}