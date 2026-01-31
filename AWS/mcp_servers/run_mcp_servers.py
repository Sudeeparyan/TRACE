"""
TRACE MCP Servers Runner

Starts all MCP servers for the TRACE system.
"""

import asyncio
import subprocess
import sys
import os
from pathlib import Path


def start_server(server_name: str, server_file: str):
    """Start an MCP server as a subprocess"""
    print(f"Starting {server_name}...")
    
    server_path = Path(__file__).parent / server_file
    
    process = subprocess.Popen(
        [sys.executable, str(server_path)],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        cwd=Path(__file__).parent
    )
    
    return process


def main():
    """Start all MCP servers"""
    print("=" * 60)
    print("TRACE MCP Servers")
    print("=" * 60)
    
    servers = [
        ("Telemetry Server", "telemetry_server.py"),
        ("Tower Config Server", "tower_config_server.py"),
        ("Energy Server", "energy_server.py"),
        ("Policy Server", "policy_server.py"),
    ]
    
    processes = []
    
    for name, file in servers:
        try:
            proc = start_server(name, file)
            processes.append((name, proc))
            print(f"  ✓ {name} started (PID: {proc.pid})")
        except Exception as e:
            print(f"  ✗ {name} failed: {e}")
    
    print()
    print("All servers started. Press Ctrl+C to stop.")
    print()
    
    try:
        while True:
            asyncio.get_event_loop().run_until_complete(asyncio.sleep(1))
    except KeyboardInterrupt:
        print("\nShutting down servers...")
        for name, proc in processes:
            proc.terminate()
            print(f"  ✓ {name} stopped")
        print("Done.")


if __name__ == "__main__":
    main()
