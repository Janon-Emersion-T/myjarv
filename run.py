#!/usr/bin/env python3
import os
import shutil
import signal
import socket
import subprocess
import sys
import time
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent
BRAIN_DIR = ROOT_DIR / "apps" / "brain"
DESKTOP_DIR = ROOT_DIR / "apps" / "desktop"
VENV_PYTHON = BRAIN_DIR / "venv" / "bin" / "python"


def require_path(path: Path, message: str) -> None:
    if not path.exists():
        raise SystemExit(message)


def require_command(name: str, message: str) -> None:
    if shutil.which(name) is None:
        raise SystemExit(message)


def stream_label(process_name: str) -> str:
    return f"[{process_name}]"


def find_available_port(host: str, preferred_port: int) -> int:
    for port in range(preferred_port, preferred_port + 50):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                sock.bind((host, port))
            except OSError:
                continue
            return port
    raise SystemExit(f"No free port found for host {host} starting at {preferred_port}.")


def start_process(name: str, command: list[str], cwd: Path) -> subprocess.Popen[bytes]:
    print(f"{stream_label(name)} starting: {' '.join(command)}")
    return subprocess.Popen(command, cwd=cwd)


def terminate_process(name: str, process: subprocess.Popen[bytes]) -> None:
    if process.poll() is not None:
        return

    print(f"{stream_label(name)} stopping")
    process.terminate()

    try:
        process.wait(timeout=10)
    except subprocess.TimeoutExpired:
        print(f"{stream_label(name)} force killing")
        process.kill()
        process.wait()


def main() -> int:
    require_path(
        VENV_PYTHON,
        "Missing backend venv Python at apps/brain/venv/bin/python. Create the venv first.",
    )
    require_path(
        DESKTOP_DIR / "package.json",
        "Missing frontend package.json at apps/desktop/package.json.",
    )
    require_command("npm", "npm is required to start the frontend.")

    if not (DESKTOP_DIR / "node_modules").exists():
        print("[frontend] node_modules missing, running npm install")
        install = subprocess.run(["npm", "install"], cwd=DESKTOP_DIR)
        if install.returncode != 0:
            return install.returncode

    backend_host = os.getenv("HOST", "127.0.0.1")
    requested_backend_port = int(os.getenv("PORT", "8000"))
    frontend_host = os.getenv("FRONTEND_HOST", "127.0.0.1")
    requested_frontend_port = int(os.getenv("FRONTEND_PORT", "1420"))
    reload_enabled = os.getenv("RELOAD", "true").lower() == "true"
    backend_port = find_available_port(backend_host, requested_backend_port)
    frontend_port = find_available_port(frontend_host, requested_frontend_port)

    if backend_port != requested_backend_port:
        print(
            f"[backend] port {requested_backend_port} is busy, using {backend_port} instead"
        )
    if frontend_port != requested_frontend_port:
        print(
            f"[frontend] port {requested_frontend_port} is busy, using {frontend_port} instead"
        )

    backend_command = [
        str(VENV_PYTHON),
        "-m",
        "uvicorn",
        "app.main:app",
        "--app-dir",
        str(BRAIN_DIR),
        "--host",
        backend_host,
        "--port",
        str(backend_port),
    ]
    if reload_enabled:
        backend_command.append("--reload")

    frontend_command = [
        "npm",
        "run",
        "dev",
        "--",
        "--host",
        frontend_host,
        "--port",
        str(frontend_port),
    ]

    processes: list[tuple[str, subprocess.Popen[bytes]]] = []

    def shutdown(*_: object) -> None:
        for name, process in reversed(processes):
            terminate_process(name, process)
        raise SystemExit(0)

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    processes.append(("backend", start_process("backend", backend_command, ROOT_DIR)))
    processes.append(("frontend", start_process("frontend", frontend_command, DESKTOP_DIR)))

    print(f"[backend] http://{backend_host}:{backend_port}")
    print(f"[frontend] http://{frontend_host}:{frontend_port}")
    print("[run.py] Press Ctrl+C to stop both processes.")

    try:
        while True:
            for name, process in processes:
                return_code = process.poll()
                if return_code is not None:
                    print(f"{stream_label(name)} exited with code {return_code}")
                    for other_name, other_process in reversed(processes):
                        if other_process is not process:
                            terminate_process(other_name, other_process)
                    return return_code
            time.sleep(1)
    except KeyboardInterrupt:
        shutdown()
    return 0


if __name__ == "__main__":
    sys.exit(main())
