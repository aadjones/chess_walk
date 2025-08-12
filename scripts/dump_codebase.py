#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script to traverse a Python codebase, ensure each .py file starts with
a comment containing its filename, and concatenate all processed files
into a single output text file, skipping specified directories.
"""

import os
import sys
import argparse
import io  # Using io.open for explicit encoding control is good practice

# --- Default Configuration ---
# Common directories to skip by default
DEFAULT_SKIP_DIRS = [
    ".git",
    "__pycache__",
    "venv",
    ".venv",
    "env",
    ".env",
    "build",
    "dist",
    "node_modules",
    ".svn",
    ".hg",
    ".pytest_cache",
    ".mypy_cache",
    ".tox",
    "site-packages",
    "lib",
    "include",
    "bin",
    "logs",
    "deprecated",
    "output",
    "reports",  # Common venv dirs
]

# --- Core Processing Functions ---


def process_python_file(file_path, filename):
    """
    Reads a Python file, ensures it starts with '# filename.py\n',
    and returns the processed content with a footer comment.

    Args:
        file_path (str): The full path to the Python file.
        filename (str): The name of the Python file (e.g., 'module.py').

    Returns:
        str: The processed file content including header and footer,
             ready for concatenation. Returns None if an error occurs.
    """
    header_comment = f"# {filename}\n"
    # Use '\n' before the # for better separation, and two newlines after
    footer_comment = f"\n# --- End of file: {filename} ---\n\n"
    processed_content = None

    try:
        # Use io.open for explicit encoding and error handling
        with io.open(file_path, "r", encoding="utf-8", errors="replace") as infile:
            file_content = infile.read()

        # Check if the exact header is present
        if not file_content.startswith(header_comment):
            # Prepend header if missing (handles empty files too)
            processed_content = header_comment + file_content
        else:
            # Header exists, use content as is
            processed_content = file_content

        # Ensure the final output chunk ends with the footer
        return processed_content + footer_comment

    except IOError as e:
        print(f"Warning: Could not read file {file_path}: {e}", file=sys.stderr)
        return None
    except Exception as e:  # Catch potential unexpected errors
        print(f"Warning: Error processing file {file_path}: {e}", file=sys.stderr)
        return None


def process_codebase(root_dir, output_file_path, skip_set):
    """
    Traverses the codebase, processes Python files, and writes to the output file.

    Args:
        root_dir (str): The root directory of the codebase.
        output_file_path (str): The path to the file where the dump will be written.
        skip_set (set): A set of directory names to skip during traversal.

    Returns:
        tuple(int, int) or None: A tuple containing (processed_file_count, skipped_file_count)
                                 on success, or None if the output file cannot be opened.
    """
    processed_count = 0
    skipped_count = 0

    try:
        # Open the output file for writing
        with io.open(output_file_path, "w", encoding="utf-8") as outfile:
            print("Starting directory traversal...")

            for dirpath, dirnames, filenames in os.walk(root_dir, topdown=True):
                # --- Directory Skipping ---
                # Modify dirnames in-place to prevent os.walk from descending
                original_dirnames_count = len(dirnames)
                dirnames[:] = [d for d in dirnames if d not in skip_set]
                if len(dirnames) < original_dirnames_count:
                    skipped_dirs = original_dirnames_count - len(dirnames)
                    # print(f"  Skipping {skipped_dirs} subdirectories in {os.path.relpath(dirpath, root_dir)}")

                # --- File Processing ---
                relative_dir = os.path.relpath(dirpath, root_dir)
                # Handle root case where relative_dir is '.'
                if relative_dir == ".":
                    relative_dir = ""

                # Sort filenames for deterministic output order (optional but nice)
                filenames.sort()

                for filename in filenames:
                    if filename.endswith(".py"):
                        full_path = os.path.join(dirpath, filename)
                        relative_file_path = os.path.join(relative_dir, filename) if relative_dir else filename

                        print(f"  Processing: {relative_file_path}...")

                        # Process the individual file
                        output_chunk = process_python_file(full_path, filename)

                        if output_chunk is not None:
                            outfile.write(output_chunk)
                            processed_count += 1
                        else:
                            # Error message was already printed by process_python_file
                            skipped_count += 1

            print("Directory traversal complete.")
            return processed_count, skipped_count

    except IOError as e:
        print(f"Error: Could not open output file {output_file_path} for writing: {e}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"An unexpected error occurred during codebase processing: {e}", file=sys.stderr)
        return None


# --- Argument Parsing and Main Execution ---


def parse_arguments():
    """Parses command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Concatenate all Python files in a directory tree into a single file, adding filename headers.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,  # Shows defaults in help
    )
    parser.add_argument("root_dir", help="Path to the root directory of the Python codebase.")
    parser.add_argument("output_file", help="Path to the output file where the concatenated code will be saved.")
    parser.add_argument(
        "--skip",
        nargs="+",
        default=DEFAULT_SKIP_DIRS,
        help="List of directory names to skip (e.g., venv __pycache__ .git).",
    )
    return parser.parse_args()


def main():
    """Main execution function."""
    args = parse_arguments()

    # Convert skip list to a set for efficient lookup
    skip_set = set(args.skip)

    # Validate root directory exists
    if not os.path.isdir(args.root_dir):
        print(f"Error: Root directory not found or not a directory: {args.root_dir}", file=sys.stderr)
        sys.exit(1)

    # Validate output file's directory exists (optional but good practice)
    output_dir = os.path.dirname(args.output_file)
    if output_dir and not os.path.isdir(output_dir):
        try:
            os.makedirs(output_dir)
            print(f"Created output directory: {output_dir}")
        except OSError as e:
            print(f"Error: Could not create output directory {output_dir}: {e}", file=sys.stderr)
            sys.exit(1)

    print("-" * 60)
    print("Starting Python Codebase Dump")
    print("-" * 60)
    print(f"Source Root:      {os.path.abspath(args.root_dir)}")
    print(f"Output File:      {os.path.abspath(args.output_file)}")
    print(f"Skipping Dirs:    {', '.join(sorted(list(skip_set)))}")
    print("-" * 60)

    # Process the codebase
    result = process_codebase(args.root_dir, args.output_file, skip_set)

    print("-" * 60)
    if result is not None:
        processed_count, skipped_count = result
        print("Dump Generation Summary:")
        print(f"  Successfully processed files: {processed_count}")
        print(f"  Skipped files due to errors:  {skipped_count}")
        print(f"  Output saved to:              {os.path.abspath(args.output_file)}")
        print("Dump complete.")
        sys.exit(0)
    else:
        print("Dump generation failed due to errors (see messages above).")
        sys.exit(1)


if __name__ == "__main__":
    main()
