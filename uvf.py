import os
from os import PathLike
from typing import Union
from typing import BinaryIO
from typing import Iterator
from typing import AnyStr
from typing import Optional
from typing import TypeAlias

VERSION = "0.1.0"
_ASSETS_EXT = ".assets"

PathType: TypeAlias = Union[AnyStr, PathLike[AnyStr]]


def main():
    args = _get_args()
    if args.check_all:
        version_map = {}
        top_version = None

        count = 0
        for assets_file in walk_assets_files(args.root):
            if version := parse_unity_version(assets_file):
                if version in version_map:
                    total = version_map[version] + 1
                    version_map[version] = total
                    if total > version_map[top_version]:
                        top_version = version
                else:
                    version_map[version] = 1
                    if not top_version:
                        top_version = version
            count += 1

        if top_version:
            print(str(version_map[top_version]) + " out of " + str(count) + " assets files agree, \"" + top_version + "\" is the Unity build version.")
        elif count > 0:
            print("Failed to parse Unity build version from " + str(count) + " assets files.")
        else:
            print("Failed to find an assets file in " + args.root)
    else:
        if assets_file := find_any_assets_file(args.root):
            print("Assets file: " + assets_file)
            if (version := parse_unity_version(assets_file)):
                print("Unity build version: " + version)
            else:
                print("Failed to parse Unity build version.")
        else:
            print("Could not find an assets file in " + args.root)


def _get_args():
    from argparse import ArgumentParser
    parser = ArgumentParser(description="Parses an assets file to discover the Unity build version")
    parser.add_argument(
        "root",
        help="root game directory"
    )
    parser.add_argument(
        "-a",
        dest="check_all",
        action="store_true",
        default=False,
        help="exhaustively check every assets file, for extra sanity"
    )
    parser.add_argument(
        "-v",
        action="version",
        version=VERSION
    )
    return parser.parse_args()


def _read_c_string(f: BinaryIO) -> str:
    return b''.join(iter(lambda: f.read(1), b'\x00')).decode("utf-8")


def parse_unity_version(assets_file: PathType) -> str:
    with open(assets_file, "rb") as f:
        f.seek(0x14)  # magic sauce
        return _read_c_string(f)


def find_any_assets_file(root: PathType) -> Optional[PathType]:
    for assets_file in walk_assets_files(root):
        return assets_file
    return None


def walk_assets_files(root: PathType) -> Iterator[PathType]:
    for dirpath, _, filenames in os.walk(root):
        for filename in filenames:
            if os.path.splitext(filename)[1] == _ASSETS_EXT:
                yield os.path.join(dirpath, filename)


if __name__ == "__main__":
    main()
