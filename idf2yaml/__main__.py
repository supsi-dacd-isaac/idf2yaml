# idf2yaml/__main__.py

import os
import argparse
from .core import idf2yaml, yaml2idf, DEFAULT_IDD
import sys


def main():

    parser = argparse.ArgumentParser(description="Convert between .idf and .yaml formats")

    mode_group = parser.add_mutually_exclusive_group(required=True)

    mode_group.add_argument("-i2y", "--idf2yaml", action="store_true", help="Convert from .idf format to .yaml format")

    mode_group.add_argument("-y2i", "--yaml2idf", action="store_true", help="Convert from .yaml format to .idf format")
    parser.add_argument("input_file", help="Path to the input file")

    parser.add_argument("-o", "--output", help="Optional output file name (default: auto-generated)")

    parser.add_argument("-s", "--silent", action="store_true", help="Silent mode (no stdout output)")

    parser.add_argument("-i", "--idd", help="Path to the EnergyPlus IDD file (default: %s)" % DEFAULT_IDD)

    parser.add_argument("-m", "--memo", action="store_true", help="Insert memo field in the output (only for -i2y)")

    parser.add_argument(
        "-e", "--include-empty", action="store_true", help="Include empty fields in the output (only for -i2y)"
    )

    args = parser.parse_args()

    # define output file
    if args.output is None:
        output_file = os.path.splitext(args.input_file)[0] + ".yaml" if args.idf2yaml else ".idf"
    else:
        output_file = args.output

    # check if input file exists
    if not os.path.isfile(args.input_file):
        if not args.silent:
            print(f"File '{args.input_file}' is not a valid path and cannot be processed. Exiting...")
        sys.exit(1)

    # manage idd file
    if args.idd is None:
        idd = DEFAULT_IDD
    elif not os.path.isfile(args.idd):
        if not args.silent:
            print(f"Idd File '{args.idd}' is not a valid path and cannot be processed. Exiting...")
        sys.exit(1)
    else:
        idd = args.idd

    # run the program
    if args.idf2yaml:
        idf2yaml(args.input_file, idd=idd, output_path=output_file, insert_memo=args.memo, skip_empty=not args.include_empty)
    elif args.yaml2idf:
        yaml2idf(args.input_file, idd=idd, output_path=output_file)

    # print success message
    if not args.silent:
        print(f"File '{args.input_file}' has been converted to '{output_file}'.")


if __name__ == "__main__":
    main()
