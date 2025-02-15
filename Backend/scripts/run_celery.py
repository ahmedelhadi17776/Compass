import os
import subprocess
from typing import List, Dict


def start_celery_workers(queues: List[Dict[str, int]]):
    """
    Start Celery workers for different queues with specified concurrency.
    """
    processes = []

    for queue_config in queues:
        for queue_name, concurrency in queue_config.items():
            # Construct the Celery worker command
            cmd = [
                "celery",
                "-A",
                "core.celery_app",
                "worker",
                "--loglevel=info",
                f"--concurrency={concurrency}",
                f"--queues={queue_name}",
                f"--hostname=worker-{queue_name}@%h"
            ]

            # Start the worker process
            process = subprocess.Popen(
                cmd,
                env=os.environ.copy(),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            processes.append(process)

    return processes


def start_celery_beat():
    """
    Start Celery beat for scheduled tasks.
    """
    cmd = [
        "celery",
        "-A",
        "core.celery_app",
        "beat",
        "--loglevel=info"
    ]

    process = subprocess.Popen(
        cmd,
        env=os.environ.copy(),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    return process


def start_flower():
    """
    Start Flower for monitoring Celery.
    """
    cmd = [
        "celery",
        "-A",
        "core.celery_app",
        "flower",
        "--port=5555"
    ]

    process = subprocess.Popen(
        cmd,
        env=os.environ.copy(),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    return process


if __name__ == "__main__":
    # Configure queue concurrency
    queue_config = [
        {"email": 2},        # 2 workers for email queue
        {"workflow": 3},     # 3 workers for workflow queue
        {"ai": 2},          # 2 workers for AI tasks
        {"notification": 2},  # 2 workers for notifications
        {"default": 1}      # 1 worker for default queue
    ]

    # Start workers
    worker_processes = start_celery_workers(queue_config)

    # Start beat scheduler
    beat_process = start_celery_beat()

    # Start Flower monitoring
    flower_process = start_flower()

    try:
        # Keep the script running
        for process in worker_processes + [beat_process, flower_process]:
            process.wait()
    except KeyboardInterrupt:
        # Gracefully shutdown on Ctrl+C
        for process in worker_processes + [beat_process, flower_process]:
            process.terminate()
            process.wait()
