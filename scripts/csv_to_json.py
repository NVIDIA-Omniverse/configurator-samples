# SPDX-FileCopyrightText: Copyright (c) 2024 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: LicenseRef-NvidiaProprietary
#
# NVIDIA CORPORATION, its affiliates and licensors retain all intellectual
# property and proprietary rights in and to this material, related
# documentation and any modifications thereto. Any use, reproduction,
# disclosure or distribution of this material and related documentation
# without an express license agreement from NVIDIA CORPORATION or
# its affiliates is strictly prohibited.

"""
This script will convert CSV files containing configurator package information to JSON for use by a React application. 
The CSV files define what data is needed and how it needs to be structured in order to be converted to a usable JSON format. 
This script requires two CSV files to execute: an "Options" and "Packages" CSVs.

Version: 1.0.0
"""

import csv
import json


OPTIONS_COLUMNS = {0: "id",
                   1: "prim_path",
                   2: "variant_set",
                   3: "option",
                   4: "variant",
                   5: "display_name",
                   }

PACKAGE_KEY_DISPLAY_NAME = "display_name"
PACKAGE_KEY_OPTIONS = "options"


def get_raw_options(options_csv_path: str) -> dict:
    """
    Returns a dictionary containing the values from an Options CSV
    """
    options_dict: dict = {}

    with open(options_csv_path, mode='r', newline='') as options_file:
        csv_reader = csv.reader(options_file)

        # Skip the header row
        next(csv_reader)

        for row in csv_reader:
            row_id: int = int(row[0])
            options_dict[row_id] = row

    return options_dict


def get_raw_packages(packages_csv_path: str) -> dict:
    """
    Returns a dictionary containing the values from a Packages CSV
    """
    packages_dict: dict = {}

    with open(packages_csv_path, mode='r', newline='') as options_file:
        csv_reader = csv.reader(options_file)

        # Skip the header row
        next(csv_reader)

        for row in csv_reader:
            # row_id: int = int(row[0])  # this is probably not needed
            package: str = row[1]
            packages_dict[package] = [int(i) for i in row[2:]]

    return packages_dict


def get_packages_with_options(options: dict, packages: dict) -> dict:
    """
    Returns a dictionary that combines Options CSV data with Packages CSV data
    """
    package_info = {}
    for package, option_ids in packages.items():
        package_info[package] = []
        for option_id in option_ids:
            package_info[package].append(options[option_id])

    return package_info


def get_packages_json(package_info: dict, include_id: bool = False) -> dict:
    """
    Returns the data that's used for the packages JSON file as a dictionary
    """
    js = {}
    for package, options_list in package_info.items():
        js[package] = {PACKAGE_KEY_DISPLAY_NAME: package, PACKAGE_KEY_OPTIONS: []}
        for options in options_list:
            current_option = {}
            for index, key in OPTIONS_COLUMNS.items():
                if index == 0 and include_id is False:
                    continue

                current_option[key] = options[index]
            js[package][PACKAGE_KEY_OPTIONS].append(current_option)

    return js


def create_json(options_csv: str, packages_csv: str, output_path: str) -> None:
    """
    Creates and writes to disk the json containing package information for use by a React application.
    """
    options: dict = get_raw_options(options_csv)
    packages: dict = get_raw_packages(packages_csv)

    package_options: dict = get_packages_with_options(options, packages)
    packages_json: dict = get_packages_json(package_options)
    
    with open(output_path, 'w') as json_file:
        json_data = json.dumps(packages_json, indent=4)
        json_file.write(json_data)


if __name__ == '__main__':
    options_csv = r"..\data\concept_car_options.csv"
    packages_csv = r"..\data\concept_car_packages.csv"
    json_output = r"..\data\concept_car.json"

    create_json(options_csv, packages_csv, json_output)
