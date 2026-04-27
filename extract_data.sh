#!/bin/sh

cd tests/directory_watcher/test_registration_processor/product_dir || exit 1
for file in "$@"; do
    extracted_name=${file%%.tar.gz}
    test ! -e "$extracted_name" || { echo "Skipping $file since $extracted_name exists" && continue; }
    echo "Extracting $file"
    tar xf "$file"
done
