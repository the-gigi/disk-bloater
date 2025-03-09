import os
import time
import argparse
import uuid


def write_file(directory, file_size, file_index):
    """Write a file of given size filled with arbitrary data."""
    filename = os.path.join(directory, f"bloated_{file_index}.bin")
    print(f"Writing {file_size} bytes to {filename}...")

    with open(filename, "wb") as f:
        f.write(os.urandom(file_size))

    print(f"Finished writing {filename}")


def bloat(target_dir, initial_size, file_size, interval, total_files):
    os.makedirs(target_dir, exist_ok=True)
    write_file(target_dir, initial_size, 0)
    for i in range(1, total_files):
        time.sleep(interval)
        write_file(target_dir, file_size, i)

def main():
    parser = argparse.ArgumentParser(description="Disk Bloater")
    parser.add_argument("--directory", required=True, help="Target directory to write files")
    parser.add_argument("--initial-size", type=int, required=True,
                        help="Initial file size in bytes")
    parser.add_argument("--file-size", type=int, required=True,
                        help="Size of subsequent files in bytes")
    parser.add_argument("--interval", type=int, required=True,
                        help="Delay between writes in seconds")
    parser.add_argument("--total-files", type=int, required=True,
                        help="Stop after writing that many files")
    args = parser.parse_args()

    bloat(args.directory, args.initial_size, args.file_size, args.interval, args.total_files)

    # just hang around forever
    while True:
        time.sleep(1)

def test():
    bloat("/tmp/bloat", 4 * 2 ** 30, 2 ** 30, 60, 5)

if __name__ == "__main__":
    #test()
    main()
