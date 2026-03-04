#!/usr/bin/env python3
"""
Utility script to switch between database and CSV data sources.
Usage: python switch_data_source.py [database|csv]
"""

import sys
import os
from pathlib import Path

def switch_data_source(mode):
    """Switch the data source configuration."""
    if mode not in ['database', 'csv']:
        print("Error: Mode must be 'database' or 'csv'")
        sys.exit(1)
    
    env_file = Path('.env')
    if not env_file.exists():
        print("Error: .env file not found")
        sys.exit(1)
    
    # Read current .env content
    content = env_file.read_text()
    lines = content.split('\n')
    
    # Find and replace DATA_SOURCE line
    new_lines = []
    data_source_found = False
    
    for line in lines:
        if line.startswith('DATA_SOURCE='):
            new_lines.append(f'DATA_SOURCE={mode}')
            data_source_found = True
        else:
            new_lines.append(line)
    
    # Add DATA_SOURCE if not found
    if not data_source_found:
        new_lines.append(f'DATA_SOURCE={mode}')
    
    # Write back to .env
    env_file.write_text('\n'.join(new_lines))
    print(f"✅ Data source switched to: {mode.upper()}")

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: python switch_data_source.py [database|csv]")
        sys.exit(1)
    
    switch_data_source(sys.argv[1])
