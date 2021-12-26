import os
from os import PathLike
import re
from typing import Union
from typing import BinaryIO
from typing import Iterator
from typing import Tuple
from typing import AnyStr
from typing import Optional
from typing import TypeAlias

VERSION = "0.1.0"
REPO_URL = "https://github.com/jrobinson3k1/UnityVersionFinderPy"

_ASSETS_EXT = ".assets"
_KNOWN_SEEK_POSITIONS = [0x14, 0x30]
_SEM_VER_PATTERN = r"^(?P<major>0|[1-9]\d*)\.(?P<minor>0|[1-9]\d*)\.(?P<patch>0|[1-9]\d*)"

PathType: TypeAlias = Union[AnyStr, PathLike[AnyStr]]


def main():
    args = _get_args()
    if args.check_all:
        version_map = {}
        top_result = None

        count = 0
        for assets_file in walk_assets_files(args.root):
            if result := parse_unity_version(assets_file):
                version = result[1]
                if version in version_map:
                    total = version_map[version] + 1
                    version_map[version] = total
                    if total > version_map[version]:
                        top_result = version
                else:
                    version_map[version] = 1
                    if not top_result:
                        top_result = result
            count += 1

        if top_result:
            print(str(version_map[top_result[1]]) + " out of " + str(count) + " assets files agree, \"" + top_result[1] + "\" is the Unity build version.")
            _check_unknown_position(top_result[0], top_result[1])
        elif count > 0:
            print("Failed to parse Unity build version from " + str(count) + " assets files.")
        else:
            print("Failed to find an assets file in " + args.root)
    else:
        if assets_file := find_any_assets_file(args.root):
            if (result := parse_unity_version(assets_file)):
                print("Unity build version: " + result[1])
                _check_unknown_position(result[0], result[1])
            else:
                print("Failed to parse Unity build version.")
        else:
            print("Could not find an assets file in " + args.root)


def _check_unknown_position(position: int, version: str):
    if position not in _KNOWN_SEEK_POSITIONS:
        print("\n\nYou found an unknown version location! Please consider sharing the following data with me so I can improve the reliablity of this script.")
        print("* Unity build version: " + version)
        print("* Seek start position: " + str(position))
        print("* The name of the game this script was performed on")
        print(REPO_URL + "\n\n")


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


def validate(value: str) -> bool:
    return True if re.match(_SEM_VER_PATTERN, value) else False


def find_any_assets_file(root: PathType) -> Optional[PathType]:
    for assets_file in walk_assets_files(root):
        return assets_file
    return None


def walk_assets_files(root: PathType) -> Iterator[PathType]:
    for dirpath, _, filenames in os.walk(root):
        for filename in filenames:
            if os.path.splitext(filename)[1] == _ASSETS_EXT:
                yield os.path.join(dirpath, filename)


def parse_unity_version(assets_file: PathType) -> Optional[Tuple[int, str]]:
    with open(assets_file, "rb") as f:
        if value := _parse_known_unity_version_positions(f) or (value := _crawl_unity_version_positions(f)):
            return value
    return None


def _parse_known_unity_version_positions(f: BinaryIO) -> Optional[Tuple[int, str]]:
    for position in _KNOWN_SEEK_POSITIONS:
        f.seek(position)
        if (value := _read_c_string(f)) and validate(value):
            return position, value
    return None


def _crawl_unity_version_positions(f: BinaryIO, stop: int = -1) -> Optional[Tuple[int, str]]:
    if stop == -1:
        f.seek(0, os.SEEK_END)
        stop = f.tell() - 0x14

    for position in range(0x00, stop, 0x04):
        f.seek(position)
        if (value := _read_c_string(f)) and validate(value):
            return position, value
    return None


def _read_c_string(f: BinaryIO) -> str:
    return b''.join(iter(lambda: f.read(1), b'\x00')).decode("utf-8")


if __name__ == "__main__":
    main()
