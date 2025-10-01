import pytest
import asyncio
from ska_dlm_client.configdb_watcher import watch_dependency_state
from ska_sdp_config import Config
import athreading
import time

@athreading.iterate
def agenerator():
    while True:
        yield 1
        time.sleep(1)

@pytest.mark.asyncio
async def test_configdb_watcher():
    config = Config()

    with pytest.raises(asyncio.TimeoutError):
        async with asyncio.timeout(3):
            # async with (
            #     watch_dependency_state(config) as producer
            # ):
            async with agenerator() as producer:
                await asyncio.sleep(10)
            #     async for key, dependency_state in producer:
            #         print(key, dependency_state)

    print("done")