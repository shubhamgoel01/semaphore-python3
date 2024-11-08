#!/usr/bin/env python3

import subprocess

def run_command(command):
    """Run a Linux command and return the output."""
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        return result.stdout.strip()
    except Exception as e:
        return "Error: {}".format(str(e))

# Basic system information
def get_basic_info():
    hostname = run_command("hostname")
    os_info = run_command("cat /etc/os-release | grep PRETTY_NAME | awk -F'=' '{print $2}' | tr -d '\"'")
    kernel_version = run_command("uname -r")

    print("Hostname: {}".format(hostname))
    print("Operating System: {}".format(os_info))
    print("Kernel Version: {}".format(kernel_version))

# CPU and memory information
def get_cpu_memory_info():
    cpu_model = run_command("lscpu | grep 'Model name' | awk -F: '{print $2}'")
    memory_info = run_command("free -h | grep Mem | awk '{print $2}'")

    print("CPU Model: {}".format(cpu_model.strip()))
    print("Total Memory: {}".format(memory_info))

# Disk usage information
def get_disk_info():
    disk_usage = run_command("df -h / | tail -1 | awk '{print $5}'")

    print("Root Disk Usage: {}".format(disk_usage))

if __name__ == "__main__":
    print("Basic VM Information:\n")
    get_basic_info()
    get_cpu_memory_info()
    get_disk_info()
    print("\nInformation collection completed.")
