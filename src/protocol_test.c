#include <stdio.h>
#include <string.h>
#include "protocol.h"

int main(void) {

    const char sequence[] = "111100001010";

    size_t preamble_length = strlen(PREAMBLE);

    if (strncmp(sequence, PREAMBLE, preamble_length) != 0) {
        printf("Invalid preamble\n");
        return 1;
    }

    printf("Valid preamble\n");

    printf("Message: %s\n", sequence + preamble_length);

    return 0;
}