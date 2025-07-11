#!/bin/bash

cd "$(dirname "$0")" || exit

docker build -t downloads.unstructured.io/unstructured-io/unstructured:app .