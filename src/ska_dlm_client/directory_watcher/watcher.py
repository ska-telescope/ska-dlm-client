"""Watcher"""

import json
import logging
from typing import Any, Dict, List

import requests
import ska_sdp_metadata_generator as metagen
from fastapi import FastAPI
from ska_sdp_dataproduct_metadata import MetaData

from ska_dlm.dlm_storage.dlm_storage_requests import rclone_access
from ska_dlm.typer_types import JsonObjectOption

from .. import CONFIG
from ..data_item import set_metadata, set_state, set_uri
from ..dlm_db.db_access import DB
from ..dlm_request import query_data_item, query_exists
from ..dlm_storage import check_storage_access, query_storage
from ..exceptions import InvalidQueryParameters, UnmetPreconditionForOperation, ValueAlreadyInDB


from watchfiles import watch


from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler


JsonType = Dict[str, Any] | List[Any] | str | int | float | bool | None
logger = logging.getLogger(__name__)

app = FastAPI()

SIMULTANEOUS_INGEST_REQUESTS = 2

def doSomethingWithNewEntry(entry):
    pass

def watch():
    for changes in watch('./path/to/dir'):
        print(changes)



import asyncio
from watchfiles import awatch

async def main():
    async for changes in awatch('/path/to/dir'):
        print(changes)

asyncio.run(main())



from watchfiles import run_process

def foobar(a, b, c):
    ...

if __name__ == '__main__':
    run_process('./path/to/dir', target=foobar, args=(1, 2, 3))


import asyncio
from watchfiles import arun_process

def foobar(a, b, c):
    ...

async def main():
    await arun_process('./path/to/dir', target=foobar, args=(1, 2, 3))

if __name__ == '__main__':
    asyncio.run(main())



class MyHandler(FileSystemEventHandler):
    db: Session

    def __init__(self, target_folder_path, db: Session = Depends(get_session)):
        super().__init__()
        self.target_folder_path = target_folder_path
        self.db = db

    def on_created(self, event):
        print(f"File {event.src_path} has been created in {self.target_folder_path}")

    def on_modified(self, event):
        print(f"File {event.src_path} has been modified in {self.target_folder_path}")


class WatchdogThread:
    def __init__(self, target_folder_path):
        self.observer = Observer()
        self.target_folder_path = target_folder_path

    def start(self):
        event_handler = MyHandler(self.target_folder_path)
        self.observer.schedule(event_handler, self.target_folder_path, recursive=True)
        print(f"Starting the folder monitoring for {self.target_folder_path}")
        self.observer.start()

    def stop(self):
        self.observer.stop()
        print(f"Stopping the folder monitoring for {self.target_folder_path}")
        self.observer.join()

target_folder_path = "/monitored"

watchdog_thread = WatchdogThread(target_folder_path)

# added this to start the monitoring.
@app.on_event("startup")
async def startup_event():
    watchdog_thread.start()


@app.on_event("shutdown")
async def shutdown_event():
    watchdog_thread.stop()

def main():
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, access_log=True, reload=True)


if __name__ == "__main__":
    main()
