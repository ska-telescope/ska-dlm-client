#!/bin/sh

SOURCE_DIR="data"
TARGET_DIR="tests/registration_processor/product_dir/product/eb-00000000/ska-sdp"
PB_ID="pb-test-20260126-24294"
PB_REGO_ID="pb-test-20260126-24295"
mkdir -p "$TARGET_DIR"

for filepath in "$SOURCE_DIR"/*.tar.*; do
    file=$(basename "$filepath")
    extracted_name=${file%.tar.*}

    if [ -e "$TARGET_DIR/$extracted_name" ]; then # Check if the extracted directory already exists in TARGET_DIR
        echo "Skipping extraction of $file since $extracted_name exists" # If it exists, skip extraction
        continue
    fi

    echo "Extracting $file into $TARGET_DIR"
    tar xf "$filepath" -C "$TARGET_DIR"
done

SRC_PRODUCT_DIR="$TARGET_DIR/$PB_ID"
DST_PRODUCT_DIR="$TARGET_DIR/$PB_REGO_ID"
if [ -d "$SRC_PRODUCT_DIR" ] && [ ! -d "$DST_PRODUCT_DIR" ]; then
    echo "Copying $PB_ID to $PB_REGO_ID for registration-only tests"
    mkdir -p "$DST_PRODUCT_DIR"
    cp -a "$SRC_PRODUCT_DIR/." "$DST_PRODUCT_DIR/"
fi
