#!/bin/sh

SOURCE_DIR="data"
TARGET_DIR="tests/registration_processor/product_dir"
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