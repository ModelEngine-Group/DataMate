#!/bin/bash

docker build -t downloads.unstructured.io/unstructured-io/unstructured:app . -f scripts/image/unstructured/Dockerfile
