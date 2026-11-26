#include <stdio.h>
#include <string.h>
#include "protocol.h"

double calculate_ber(const char *expected, const char *observed) {

    int errors = 0;
    int length = strlen(expected);

    if (length == 0 || strlen(observed) != strlen(expected)) {
        return -1;
    }

    for (int i = 0; i < length; i++) {
        if (expected[i] != observed[i]) {
            errors++;
        }
    }

    return (double)errors / length;
}

int main(void) {

    const char *expected = "10101010";

    const char *test_cases[] = {
        "10101010",
        "10101011",
        "10001011",
        "01010101"
    };

    for (int i = 0; i < 4; i++) {

        double ber = calculate_ber(expected, test_cases[i]);

        printf("Test case %d (BER calculation example; errors are intentional)\n", i + 1);
        printf("Expected: %s\n", expected);
        printf("Observed: %s\n", test_cases[i]);
        printf("BER: %.2f%%\n", ber * 100);
        printf("Accuracy: %.2f%%\n\n", (1 - ber) * 100);
    }

    return 0;
}