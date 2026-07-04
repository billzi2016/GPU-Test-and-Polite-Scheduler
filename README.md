# GPU-Test-and-Polite-Scheduler

A beginner-friendly toolkit for shared GPU servers. It focuses on two practical jobs:

1. Check whether the GPU environment is healthy, with optional stress tests and multi-GPU communication tests.
2. Keep long-running jobs under `tmux`, and politely wait for idle GPUs before resuming work in a shared environment.

This project is useful if you often run into questions like:

- whether CUDA, drivers, and GPU topology are configured correctly
- whether a GPU can sustain load without temperature, power, OOM, or dropout issues
- whether multi-GPU communication is working as expected
- how to run long training or sampling jobs in the background without aggressively competing for shared GPUs

## What This Project Does

### 1. Environment Checks

One command shows:

- `nvidia-smi`
- `nvidia-smi topo -m`
- driver version
- CUDA version
- visible GPU list
- whether `nvidia-smi`, `tmux`, and `python3` are available

### 2. GPU Stress Tests

The stress test continuously runs matrix multiplication on selected GPUs, so you can observe:

- whether GPU utilization can stay high
- whether temperature keeps rising
- whether the machine reports GPU dropouts, errors, or OOM failures

### 3. Multi-GPU Communication Tests

The communication test runs a basic `all_reduce` test across multiple GPUs to quickly check:

- whether multiple GPUs can cooperate normally
- whether communication looks obviously abnormal
- whether topology and communication behavior line up

### 4. Polite Background Scheduling

If a task exits unexpectedly, the scheduler does not immediately force a restart. It first checks whether the target GPU is busy:

- utilization above the threshold: wait
- utilization at or below the threshold: resume the task

This behavior is designed for shared servers, where jobs should avoid directly colliding with other users.

## Who This Is For

This project is suitable for:

- users of lab or team shared GPU servers
- people who want to validate GPUs before running real jobs
- long-running training or sampling tasks that need `tmux` supervision

This project is not intended for:

- cluster-level scheduling
- full platforms such as Slurm, Kubernetes, or Ray
- multi-machine unified resource management

## Runtime Requirements

- Linux
- NVIDIA GPU
- NVIDIA driver
- `nvidia-smi`
- `tmux`
- `python3`

Basic Python dependencies:

```bash
pip install -r requirements.txt
```

Notes:

- `torch` is not pinned in `requirements.txt`
- PyTorch is tightly coupled to CUDA versions
- install the PyTorch build that matches your machine's CUDA environment

## Shortest Path for New Users

If this is your first time using the project, follow this order.

### Step 1: Check the Environment

```bash
bash scripts/test_env.sh
```

You will see:

- current `nvidia-smi`
- current `nvidia-smi topo -m`
- GPU summary information

If this step fails, fix the environment before starting training.

### Step 2: Run a Single-GPU Stress Test

```bash
bash scripts/start_stress_test.sh --gpus 0
```

Open another terminal and watch:

```bash
watch -n 1 nvidia-smi
```

Focus on:

- whether `GPU-Util` stays near high load
- whether temperature keeps rising
- whether the program exits quickly with errors

### Step 3: Run a Multi-GPU Communication Test

If you plan to use multiple GPUs, run:

```bash
bash scripts/start_comm_test.sh --gpus 0,1
```

This prints topology first, then runs the communication test.

### Step 4: Start the Scheduler

Review the example config first:

- [configs/scheduler.example.yaml](./configs/scheduler.example.yaml)

Then start the watchdog:

```bash
bash scripts/start_watchdog.sh configs/scheduler.example.yaml
```

By default, the watchdog itself is also placed in a background `tmux` session.

## Typical Workflow

You can think of the project as this workflow:

1. Use `test_env.sh` to check whether the machine is healthy.
2. Use `start_stress_test.sh` to see whether GPUs run stably.
3. Use `start_comm_test.sh` to check multi-GPU communication.
4. Make your own task resume-friendly.
5. Use `start_watchdog.sh` to supervise the task.
6. Let the task run in a shared environment with an "run when idle, yield when busy, resume after failure" pattern.

## Connecting Your Own Task to the Scheduler

The key is not simply putting a command into `tmux`. Your task itself should support resuming.

Ideally, your task should:

1. save checkpoints regularly
2. save through a temporary file plus atomic replacement to avoid corrupted checkpoint files
3. automatically load the latest valid checkpoint on startup

References:

- [examples/example_atomic_task.py](./examples/example_atomic_task.py)
- [examples/example_resume_task.sh](./examples/example_resume_task.sh)
- [docs/atomic_task_spec.md](./docs/atomic_task_spec.md)

## Configuration Files

The repository currently provides three main example configs:

- [configs/stress_test.example.yaml](./configs/stress_test.example.yaml): stress test config
- [configs/comm_test.example.yaml](./configs/comm_test.example.yaml): communication test config
- [configs/scheduler.example.yaml](./configs/scheduler.example.yaml): scheduler config

Important scheduler fields:

- `tasks`: list of supervised tasks
- `gpu_id`: target GPU bound to a task
- `command`: command to execute
- `poll_interval_seconds`: watchdog polling interval
- `gpu_busy_threshold_percent`: threshold for deciding whether a GPU may be in use

## Docker Support

The repository includes:

- [Dockerfile](./Dockerfile)
- [requirements.txt](./requirements.txt)

The current `Dockerfile` uses:

- `nvidia/cuda:12.4.1-cudnn-runtime-ubuntu22.04`

Notes:

- it is a base project image, not a fully configured production image
- `torch` is not installed by default inside the container
- real GPU usage still requires NVIDIA drivers and NVIDIA Container Toolkit on the host

## Project Structure

If you want to continue developing this project, start with:

- [PRD.md](./PRD.md): product requirements document
- [DOC_TREE.md](./DOC_TREE.md): directory structure and file responsibilities
- [TASK.md](./TASK.md): development task list

## Current Status

The repository currently includes the first version of:

- documentation
- example configs
- environment checks
- stress tests
- communication tests
- `tmux` scheduling
- watchdog supervision
- example tasks
- basic unit tests

Basic unit tests have passed.

However, these still need to be verified on the target Linux + NVIDIA machine:

- real GPU stress tests
- real NCCL multi-GPU communication
- real `tmux` background watchdog behavior

## Common Notes

### 1. Why `requirements.txt` Does Not Include `torch`

PyTorch is tightly coupled to CUDA versions. Pinning it directly would easily cause installation conflicts on other machines.

### 2. Why "Someone Else Is Using the GPU" Only Checks GPU Utilization

This is a lightweight first-version strategy. It is practical, but it can misjudge some cases. A later version could combine utilization and memory-usage thresholds.

### 3. Will This Project Preempt Other Users' GPUs?

No. The design goal is the opposite: avoid aggressively taking resources in shared environments.

## Possible Future Extensions

Natural next steps for a second version include:

- add a GPU memory-usage threshold
- add retry limits after failures
- add alerts
- add clearer task status display
- add a simple TUI or web panel

## License

This repository does not currently include a separate LICENSE file.
