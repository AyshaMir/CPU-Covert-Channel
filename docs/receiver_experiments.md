# Initial CPU Contention Experiment

## Objective

To investigate the effect of CPU scheduling and CPU affinity on program execution time.

## Experimental Environment

- Processor: Intel Core i7-1185G7
- RAM: 16 GB
- Physical cores: 4
- Logical CPUs: 8
- Operating environment: Ubuntu WSL2
- Compiler: GCC 13.3.0


## Methodology

A C benchmark performing one million additions was executed for 20 samples under three different CPU allocation configurations. Stress-ng was used to generate a competing CPU workload.

## Results

| Configuration | Average execution time |
|---|---:|
| Baseline | 3.379451 ms |
| Same CPU | 7.088560 ms |
| Separate cores | 2.911477 ms |

## Observations

Running both processes on the same logical CPU increased the benchmark execution time by approximately 109.75%. Separating the processes across different reported cores substantially reduced the observed scheduling interference.

## Limitations

The results are preliminary and may be influenced by background processes, CPU frequency changes, and WSL2 virtualization. Additional trials are required to establish reproducibility.