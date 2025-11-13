#!/usr/bin/env python3

from ska_sdp_config import Config, ConfigCollision
from ska_sdp_config.entity import ProcessingBlock, Script
from ska_sdp_config.entity.flow import DataProduct, Flow

# ---------------------------------------------------------
# Demo identifiers
# ---------------------------------------------------------

# This matches the required regex: ^pb-[a-z0-9]+-[0-9]{8}-[a-z0-9]+$
PB_ID = "pb-madeup-00000000-a"
FLOW_NAME = "demo-prod-a"

SCRIPT = Script.Key(kind="batch", name="unit_test", version="0.0.0")

# ---------------------------------------------------------
# Connect to etcd via localhost→container port mapping.
# The watcher connects via "tests-etcd-1", but my local
# test script connects through host port 2379.
# ---------------------------------------------------------

cfg = Config(host="127.0.0.1", port=2379)


# ---------------------------------------------------------
# Ensure the PB exists
# ---------------------------------------------------------

def ensure_processing_block() -> None:
    """Create the ProcessingBlock if it doesn't already exist."""
    for txn in cfg.txn():
        if txn.processing_block.get(PB_ID) is None:
            txn.processing_block.create(
                ProcessingBlock(
                    key=PB_ID,
                    eb_id=None,
                    script=SCRIPT,
                )
            )
            print(f"Created ProcessingBlock {PB_ID}")
        else:
            print(f"ProcessingBlock {PB_ID} already exists")


# ---------------------------------------------------------
# Create a Flow and set its state to FINISHED
# (This triggers the watcher.)
# ---------------------------------------------------------

def create_or_update_flow() -> None:
    """Create a Flow + set its state to FINISHED."""
    test_dataproduct = Flow(
        key=Flow.Key(pb_id=PB_ID, kind="data-product", name=FLOW_NAME),
        sink=DataProduct(data_dir="/datapath", paths=[]),
        sources=[],
        data_model="Visibility",
    )

    # Create the Flow (idempotent)
    for txn in cfg.txn():
        try:
            txn.flow.create(test_dataproduct)
            print(f"Flow created: {test_dataproduct.key}")
        except ConfigCollision:
            print(f"Flow already exists: {test_dataproduct.key}")

    # Set/update Flow state to FINISHED
    for txn in cfg.txn():
        ops = txn.flow.state(test_dataproduct.key)
        try:
            ops.create({"status": "FINISHED"})
            print("State CREATED: FINISHED")
        except Exception:
            ops.update({"status": "FINISHED"})
            print("State UPDATED: FINISHED")

    print("Done.")


# ---------------------------------------------------------
# Main
# ---------------------------------------------------------

if __name__ == "__main__":
    ensure_processing_block()
    create_or_update_flow()
