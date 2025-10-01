"""Configuration Database watcher client."""

import asyncio
import logging
from ska_sdp_config import Config
from ska_sdp_config.entity import Dependency
from typing import Generator
import athreading

logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)


@athreading.iterate
def watch_dependency_state(config: Config) -> Generator[str, str | None, None]:
    """TODO: DMAN-157
    # must run from inside SDP cluster (try dp-shared namespace)

    Args:
        config: _description_

    Yields:
        _description_
    """

    for watcher in config.watcher():
        states = []
        for txn in watcher.txn():
            try:
                for key in txn.dependency.list_keys():
                    dependency = txn.dependency.state(key)

                    # apply filtering here. WORKING → FINISHED. Any others?
                    states.append((key, dependency.state))
            except:
                raise
        yield from states