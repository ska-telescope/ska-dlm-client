from enum import Enum
import asyncio
from pathlib import Path, PosixPath
from watchfiles import awatch, Change
from typing import Set


class InternalState(Enum):
    IN_QUEUE = 0
    INGESTING = 1
    INGESTED = 2
    BAD = 3


class PathType(Enum):
    FILE = 0
    DIRECTORY = 1
    MEASUREMENT_SET = 2

def supportPathType(path: Path) -> bool:
    pass


def followSymLink(path: Path) -> Path:
    if path.is_symlink():
        path.is_dir()
        path.is_file()


def doSomethingWithNewEntry(entry: tuple[Change, str]):
    print("in do something " + entry.__str__())
    p = Path(entry[1])
    print(p)
#    pp = PosixPath(entry[1])
#    print(pp)
    if entry[0] is not Change.deleted:
        p = p.resolve()
        if p.exists():
            stat = p.stat()
            print(stat)
        else:
            print("Cannot find resolved path " + p.__str__())


async def main():
    async for changes in awatch('/Users/00077990/watcher'): # type: Set[tuple[Change, str]]
        for change in changes:
            print("in main " + change.__str__())
            doSomethingWithNewEntry(change)


asyncio.run(main(), debug=None)
