"""
CLI support for ska_dlm package.

The SKA DLM is using typer to provide a convenient user experience
on the command line, including help and command completion. After
installation of the package it can be used with the command:

```bash
$ ska-dlm-client
Usage: ska-dlm-client [OPTIONS] COMMAND [ARGS]...
Try 'ska-dlm-client --help' for help.
```
"""

import logging

import ska_ser_logging
from requests import HTTPError

from ska_dlm_client.exception_handling_typer import ExceptionHandlingTyper
from ska_dlm_client.typer_utils import dump_short_stacktrace

from .directory_watcher.main import cli as directory_app
from .kafka_watcher.main import cli as kafka_app

app = ExceptionHandlingTyper(pretty_exceptions_show_locals=False, result_callback=print)
app.add_typer(directory_app, name="ingest", help="Watch directory for new data files.")
app.add_typer(kafka_app, name="data-item", help="Watch Kafka topic for new data items.")

app.exception_handler(HTTPError)(dump_short_stacktrace)

def main():
    """SKA Data Lifecycle Management Clients command-line utility."""
    ska_ser_logging.configure_logging(level=logging.INFO)
    app()


if __name__ == "__main__":
    main()
