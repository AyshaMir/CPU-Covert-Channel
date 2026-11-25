
#!/usr/bin/env bash
set -euo pipefail

# Find repository root
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

# Compiler settings
CC="${CC:-gcc}"
CFLAGS=(-O2 -Wall -Wextra -std=c11)

# Create directory for compiled programs
mkdir -p bin

echo "=================================="
echo "CPU Covert Channel - Build"
echo "=================================="

# Compile sender
echo "Building sender..."
"$CC" "${CFLAGS[@]}" \
    src/sender.c \
    -o bin/sender

# Compile receiver
echo "Building receiver..."
"$CC" "${CFLAGS[@]}" \
    src/receiver.c \
    -o bin/receiver

# Compile legitimate workload benchmark
echo "Building benchmark..."
"$CC" "${CFLAGS[@]}" \
    src/benchmark.c \
    -o bin/benchmark \
    -lm

# Compile interference generator
echo "Building interference generator..."
"$CC" "${CFLAGS[@]}" \
    src/interference.c \
    -o bin/interference

echo ""
echo "=================================="
echo "Build completed successfully!"
echo "=================================="

echo "Executables:"
echo "  bin/sender"
echo "  bin/receiver"
echo "  bin/benchmark"
echo "  bin/interference"
