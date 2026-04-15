#!/bin/bash

DIR_NAME="$(dirname $0)"
cd "$DIR_NAME"

OUTPUT_PATH="$PWD/../../docs/swift"

sourcekitten doc --spm --module-name MySwiftLibrary > "$OUTPUT_PATH/MySwiftLibrary.json"
sourcekitten doc --spm --module-name MyOtherSwiftLibrary > "$OUTPUT_PATH/MyOtherSwiftLibrary.json"
