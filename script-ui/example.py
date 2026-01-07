#!/usr/bin/env python3
"""
Example script demonstrating various argparse argument types.

This script showcases all the different argument types that script-ui.py can handle.
Use this to test the GUI wrapper generator:

    python script-ui.py example.py
"""

import argparse
import sys


def main():
    parser = argparse.ArgumentParser(
        description="Example script with various argument types for testing script-ui.py"
    )

    # Required file arguments
    parser.add_argument('-i', '--input-file', required=True,
                       help='Input file to process (required)')
    parser.add_argument('-o', '--output-file', required=True,
                       help='Output file to create (required)')

    # Optional file arguments
    parser.add_argument('--config-file', type=str,
                       help='Optional configuration file')

    # Multiple files
    parser.add_argument('--sources', nargs='+',
                       help='One or more source files to process')

    # Directory argument
    parser.add_argument('--output-dir', type=str,
                       help='Output directory for results')

    # Boolean flags
    parser.add_argument('--verbose', action='store_true',
                       help='Enable verbose output')
    parser.add_argument('--debug', action='store_true',
                       help='Enable debug mode')
    parser.add_argument('--no-backup', dest='backup', action='store_false',
                       help='Disable backup creation')

    # Numeric arguments
    parser.add_argument('--count', type=int, default=10,
                       help='Number of items to process (default: 10)')
    parser.add_argument('--threshold', type=float, default=0.5,
                       help='Threshold value between 0.0 and 1.0 (default: 0.5)')

    # Choices (dropdown)
    parser.add_argument('--format', choices=['json', 'xml', 'csv', 'yaml'],
                       default='json',
                       help='Output format (default: json)')
    parser.add_argument('--log-level', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
                       default='INFO',
                       help='Logging level (default: INFO)')

    # String arguments
    parser.add_argument('--name', type=str, default='default',
                       help='Name for the operation (default: default)')
    parser.add_argument('--description', type=str,
                       help='Optional description')

    args = parser.parse_args()

    # Display all the arguments
    print("=" * 60)
    print("Example Script - Arguments Received")
    print("=" * 60)
    print()
    print(f"Input File:      {args.input_file}")
    print(f"Output File:     {args.output_file}")
    print(f"Config File:     {args.config_file}")
    print(f"Sources:         {args.sources}")
    print(f"Output Dir:      {args.output_dir}")
    print()
    print(f"Verbose:         {args.verbose}")
    print(f"Debug:           {args.debug}")
    print(f"Backup:          {args.backup}")
    print()
    print(f"Count:           {args.count}")
    print(f"Threshold:       {args.threshold}")
    print()
    print(f"Format:          {args.format}")
    print(f"Log Level:       {args.log_level}")
    print()
    print(f"Name:            {args.name}")
    print(f"Description:     {args.description}")
    print()
    print("=" * 60)
    print("Processing complete!")
    print("=" * 60)

    return 0


if __name__ == '__main__':
    sys.exit(main())
