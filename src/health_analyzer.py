
#!/usr/bin/env python3

import json
import os
import platform
import shutil
import subprocess
from datetime import datetime
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
REPORT_DIR = PROJECT_DIR / "reports"

# Alert thresholds
DISK_WARNING = 80
DISK_CRITICAL = 90
MEMORY_WARNING = 80
MEMORY_CRITICAL = 90


def run_command(command):
    """Run a read-only system command safely."""
    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        if result.returncode == 0:
            return result.stdout.strip()
        return None
    except (OSError, subprocess.TimeoutExpired):
        return None


def get_memory():
    """Read memory statistics from /proc/meminfo."""
    values = {}

    try:
        with open("/proc/meminfo", encoding="utf-8") as file:
            for line in file:
                key, value = line.split(":", 1)
                values[key] = int(value.strip().split()[0]) * 1024

        total = values["MemTotal"]
        available = values["MemAvailable"]
        used = total - available

        return {
            "total_bytes": total,
            "used_bytes": used,
            "available_bytes": available,
            "usage_percent": round(used / total * 100, 1),
        }
    except (OSError, KeyError, ValueError, ZeroDivisionError):
        return {"error": "Memory information unavailable"}


def get_disk():
    """Check disk usage for the root filesystem."""
    usage = shutil.disk_usage("/")

    return {
        "total_bytes": usage.total,
        "used_bytes": usage.used,
        "free_bytes": usage.free,
        "usage_percent": round(usage.used / usage.total * 100, 1),
    }


def get_top_processes():
    """List the ten processes using the most CPU."""
    output = run_command([
        "ps", "-eo", "pid,comm,%cpu,%mem",
        "--sort=-%cpu",
    ])

    if not output:
        return []

    lines = output.splitlines()[1:11]
    processes = []

    for line in lines:
        parts = line.split(None, 3)
        if len(parts) == 4:
            processes.append({
                "pid": parts[0],
                "name": parts[1],
                "cpu_percent": parts[2],
                "memory_percent": parts[3],
            })

    return processes


def get_uptime():
    """Return system uptime in seconds."""
    try:
        with open("/proc/uptime", encoding="utf-8") as file:
            return round(float(file.read().split()[0]))
    except (OSError, ValueError, IndexError):
        return None


def get_failed_services():
    """Check failed system services where systemd is available."""
    output = run_command([
        "systemctl", "--failed", "--no-legend", "--plain"
    ])

    if output is None:
        return {"available": False, "services": []}

    services = [
        line.split()[0]
        for line in output.splitlines()
        if line.split()
    ]

    return {"available": True, "services": services}


def assess_health(memory, disk, services):
    """Generate findings using simple, explainable rules."""
    findings = []

    if "usage_percent" in disk:
        usage = disk["usage_percent"]

        if usage >= DISK_CRITICAL:
            findings.append({
                "severity": "CRITICAL",
                "issue": f"Root filesystem usage is {usage}%",
                "recommendation": (
                    "Investigate large files and logs before cleanup."
                ),
            })
        elif usage >= DISK_WARNING:
            findings.append({
                "severity": "WARNING",
                "issue": f"Root filesystem usage is {usage}%",
                "recommendation": (
                    "Review disk usage and plan cleanup if needed."
                ),
            })

    if "usage_percent" in memory:
        usage = memory["usage_percent"]

        if usage >= MEMORY_CRITICAL:
            findings.append({
                "severity": "CRITICAL",
                "issue": f"Memory usage is {usage}%",
                "recommendation": (
                    "Inspect processes and memory pressure before action."
                ),
            })
        elif usage >= MEMORY_WARNING:
            findings.append({
                "severity": "WARNING",
                "issue": f"Memory usage is {usage}%",
                "recommendation": (
                    "Review memory-intensive processes."
                ),
            })

    if services["available"] and services["services"]:
        findings.append({
            "severity": "WARNING",
            "issue": (
                f"{len(services['services'])} failed system service(s)"
            ),
            "recommendation": (
                "Inspect service status and logs before restarting."
            ),
        })

    if not findings:
        findings.append({
            "severity": "OK",
            "issue": "No configured threshold violations detected",
            "recommendation": "Continue routine monitoring.",
        })

    return findings


def collect_report():
    """Collect system data and assess its current health."""
    memory = get_memory()
    disk = get_disk()
    services = get_failed_services()

    return {
        "generated_at": datetime.now().astimezone().isoformat(),
        "hostname": platform.node(),
        "operating_system": platform.platform(),
        "python_version": platform.python_version(),
        "cpu_count": os.cpu_count(),
        "uptime_seconds": get_uptime(),
        "memory": memory,
        "disk": disk,
        "top_processes": get_top_processes(),
        "failed_services": services,
        "findings": assess_health(memory, disk, services),
    }


def format_bytes(value):
    """Format bytes into readable units."""
    size = float(value)

    for unit in ("B", "KB", "MB", "GB", "TB"):
        if size < 1024 or unit == "TB":
            return f"{size:.1f} {unit}"
        size /= 1024

    return f"{size:.1f} TB"


def main():
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    report = collect_report()

    print("\n=== Linux Health Analyzer ===")
    print(f"Generated: {report['generated_at']}")
    print(f"Operating system: {report['operating_system']}")
    print(f"CPU cores: {report['cpu_count']}")
    print(f"Uptime: {report['uptime_seconds']} seconds")

    if "usage_percent" in report["memory"]:
        print(
            "Memory usage: "
            f"{report['memory']['usage_percent']}% "
            f"({format_bytes(report['memory']['used_bytes'])} used)"
        )

    print(
        f"Root disk usage: {report['disk']['usage_percent']}% "
        f"({format_bytes(report['disk']['free_bytes'])} free)"
    )

    print("\n--- Findings ---")
    for finding in report["findings"]:
        print(f"[{finding['severity']}] {finding['issue']}")
        print(f"  Recommendation: {finding['recommendation']}")

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = REPORT_DIR / f"health_report_{timestamp}.json"

    report_path.write_text(
        json.dumps(report, indent=2),
        encoding="utf-8",
    )

    print(f"\nJSON report saved to: {report_path}")


if __name__ == "__main__":
    main()
