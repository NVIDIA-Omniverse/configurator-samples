"""
Module that allows to copy the configurator elsewhere via CLI

Example usage:
python copy_configurator.py --source_file C:/configurator/product_configurator_base.usd --target_root C:/moved/configurator --overwrite
or
D:/Builds/kit-app-template/_build/windows-x86_64/release/kit/kit.exe --exec "C:/Code/configurator-samples/scripts/cache/copy_configurator.py --source_file C:/configurator/product_configurator_base.usd --target_root C:/moved/configurator --overwrite"
"""

import argparse
import pathlib
import os
import shutil

def copy_source_to_target(src_file, target_directory, overwrite=None):
    """Copies the parent directory of the passed file to the target directory and optionally overwrite if the directory already exists.

    Args:
        src_file (str): Path to the source file for the configurator
        target_directory (str): Where the parent directory of the source file should be copied to.
        overwrite (bool, optional): If passed in, the target directory will be overwritten if it already exists. Defaults to None.
    """
    parent_directory = pathlib.Path(src_file).parent.as_posix()
    if overwrite and os.path.exists(target_directory):
        print(f'Target directory exists, overwrite flag passed - removing {target_directory}')
        shutil.rmtree(target_directory)
    if not os.path.exists(target_directory):
        print(f'Starting copy:\nSource - {parent_directory}\nTarget - {target_directory}')
        shutil.copytree(parent_directory, target_directory)
        print('Copy Complete')


def main():
    parser = argparse.ArgumentParser(description="Copy source directory to target root, run UJITSU cache, check the log for errors")
    parser.add_argument("--source_file", required=True, help="The configurator source file to be copied")
    parser.add_argument("--target_root", required=True, help="The destination directory that the source directory (automatically calculated) will be copied to")
    parser.add_argument("--overwrite", action=argparse.BooleanOptionalAction, help="Overwrite if the target root folder already exists")
    args = parser.parse_args()
    copy_source_to_target(args.source_file, args.target_root, args.overwrite)

if __name__ == "__main__":
    main()