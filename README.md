# ESSR – Embedded Secure Software Repository

**ESSR** is a Python-based utility designed to automate the setup and configuration of Arduino boards for use in secure embedded applications, such as TOTP hardware tokens.

## Features

- One-step execution with `python3 TOTPin0.py`
- Automatically installs all required dependencies and libraries
- Guides the user through the setup and usage process interactively
- Detects and identifies connected Arduino boards (and their clones) by monitoring USB port changes
- Supports iterative auto-recognition of devices plugged in and out

## Getting Started

### Prerequisites

- Python 3.x
- USB-connected Arduino-compatible device

### Running the Script

To start, simply run:

```bash
python3 TOTPin0.py
```

The script will:

  Install all dependencies automatically.
  
  Guide you through the configuration process.
  
  Continuously monitor USB port changes to detect boards.
