"""Parse the log look for UJITSO log errors. 
Example usage: 
python validate_log.py --log_file C:/moved/configurator/cache_validation.log
or 
D:/Builds/kit-app-template/_build/windows-x86_64/release/kit/kit.exe --exec "C:/Code/configurator-samples/scripts/cache/validate_log.py --log_file C:/moved/configurator/cache_validation.log"
"""

import sys
import pathlib
import argparse

IGNORE_PROCESSORS = []


def parse_log(log_path: str):
    """Look through the log for errors.

    Args:
        log_path (str): Path to log file to parse

    Returns:
        list: list of errors
    """
    errors = []
    with open(log_path, "rt", encoding="utf8") as log_file:
        for line in log_file.readlines():
            if line.startswith("UJITSO: FAILED"):
                processor = line.split("Processor: '")[-1].split("' |")[0]
                # Explicitly skipping MdlToHlslProcessor
                if processor.startswith('UJITSO-v2-MdlToHlslProcessor-'):
                    print(f'Found {processor} - skipping')
                    continue
                if processor not in IGNORE_PROCESSORS:
                    errors.append(processor)

    return errors


def main():
    """
    Parse log ang return code 0 if no errors and -1 if errors.
    """
    return_code = 0
    has_errors = False
    parser = argparse.ArgumentParser(description="Parse log and return error code 0 if no issues")
    parser.add_argument("--log_file", required=True, help="Path to the log to validate")

    args = parser.parse_args()
    errors = parse_log(args.log_file)
    if errors:
        print('Errors detected:')
        for error in errors:
            print(error)
        return_code = -1
        has_errors = True
        print('Errors found')
    else:
        if IGNORE_PROCESSORS:
            print('No errors detected with the following processors supressed:')
            for ignore in IGNORE_PROCESSORS:
                print(ignore)
        print('No errors')


    if pathlib.Path(sys.executable).stem == 'kit':
        import omni.kit.app
        omni.kit.app.get_app().post_quit(return_code)
    if pathlib.Path(sys.executable).stem == 'python':
        print(f'Has errors: {has_errors}')
        return has_errors
        
if __name__ == "__main__":
    main()


