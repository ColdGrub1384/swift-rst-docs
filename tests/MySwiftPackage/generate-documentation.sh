#!/bin/bash

DIR_NAME="$(dirname $0)"
cd "$DIR_NAME"

# Default path swift-rst-docs searches for documentation in
OUTPUT_PATH="$PWD/../../docs/swift/_api"
mkdir -p "$OUTPUT_PATH"

# Generate documentation
sourcekitten doc --spm --module-name MySwiftLibrary > "$OUTPUT_PATH/MySwiftLibrary.json"
sourcekitten doc --spm --module-name MyOtherSwiftLibrary > "$OUTPUT_PATH/MyOtherSwiftLibrary.json"
