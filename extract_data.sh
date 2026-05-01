#!/bin/sh

SOURCE_DIR="data"
TARGET_DIR="tests/directory_watcher/test_registration_processor/product_dir"

for file in "$@"; do
    extracted_name=${file%%.tar.gz}

    if [ -e "$TARGET_DIR/$extracted_name" ]; then # Check if the extracted directory already exists in TARGET_DIR
        echo "Skipping extraction of $file since $extracted_name exists" # If it exists, skip extraction
        continue
    fi

    echo "Extracting $SOURCE_DIR/$file into $TARGET_DIR"
    tar xjf "$SOURCE_DIR/$file" -C "$TARGET_DIR"
done