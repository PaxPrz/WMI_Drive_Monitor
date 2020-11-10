# WMI Drive Monitor

For Windows

Monitors Drive Activity, especially for USB Drives

### Monitors:

- Insertion of Drives
- Ejection of Drives
- Size of File Copied to Drive
- Size of File Removed from Drive

## Branches:

**o single**:

Runs asynchronously using generator based subroutines.

**o thread**:

Each action is monitored by its own thread.

## Usage:

> python3.8 WMIMonitor.py -h

> python3.8 WMIMonitor.py -l -p
