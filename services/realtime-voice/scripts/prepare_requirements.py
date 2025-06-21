#!/usr/bin/env python
"""
Prepare Requirements Script

This script creates a modified requirements file that excludes problematic packages
like PyAudio, which can be installed separately.
"""
import os
import sys
import argparse
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_modified_requirements(input_file: str, output_file: str, exclude_packages: list) -> bool:
    """
    Create a modified requirements file excluding specified packages.
    
    Args:
        input_file: Path to the original requirements file
        output_file: Path to write the modified requirements file
        exclude_packages: List of package names to exclude
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        if not os.path.exists(input_file):
            logger.error(f"Input file '{input_file}' does not exist")
            return False
            
        with open(input_file, 'r') as f:
            requirements = f.readlines()
            
        # Filter out excluded packages
        filtered_requirements = []
        excluded_count = 0
        
        for line in requirements:
            line = line.strip()
            if not line or line.startswith('#'):
                filtered_requirements.append(line)
                continue
                
            # Check if line contains any of the excluded packages
            exclude = False
            for package in exclude_packages:
                if line.lower().startswith(package.lower()):
                    exclude = True
                    excluded_count += 1
                    logger.info(f"Excluding: {line}")
                    break
                    
            if not exclude:
                filtered_requirements.append(line)
                
        # Write the modified requirements file
        with open(output_file, 'w') as f:
            f.write('\n'.join(filtered_requirements))
            
        logger.info(f"Created modified requirements file: {output_file}")
        logger.info(f"Excluded {excluded_count} packages: {', '.join(exclude_packages)}")
        return True
        
    except Exception as e:
        logger.error(f"Error creating modified requirements file: {e}")
        return False

def main():
    """Main function to parse arguments and create modified requirements file."""
    parser = argparse.ArgumentParser(description='Create a modified requirements file excluding specified packages.')
    parser.add_argument('--input', '-i', default='requirements-prod.txt', help='Input requirements file')
    parser.add_argument('--output', '-o', default='requirements-no-problematic.txt', help='Output requirements file')
    parser.add_argument('--exclude', '-e', nargs='+', default=['pyaudio'], help='Packages to exclude')
    
    args = parser.parse_args()
    
    success = create_modified_requirements(args.input, args.output, args.exclude)
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())