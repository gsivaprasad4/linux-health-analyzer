# Linux Health Analyzer

A lightweight Python tool for monitoring Linux system health and identifying common resource issues.

## Features

- Collects Linux system information and uptime
- Checks memory and root disk usage
- Lists processes by resource usage
- Checks failed system services where supported
- Identifies threshold violations
- Generates timestamped JSON health reports

## Requirements

- Linux
- Python 3.10 or later

## Usage

Run the analyzer:

```bash
python3 src/health_analyzer.py
```

The tool prints a health summary and saves a JSON report in the `reports/` directory.

## Safety

The tool is designed to report system health findings without automatically restarting services, terminating processes, or deleting files.

## Project Structure

```text
linux-health-analyzer/
├── src/
│   └── health_analyzer.py
├── reports/
├── tests/
├── .gitignore
└── README.md
```

## Planned Improvements

- Add automated tests
- Add an HTML dashboard
- Improve diagnostic recommendations
