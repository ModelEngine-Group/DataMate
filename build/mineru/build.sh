#!/bin/bash

cd "$(dirname "$0")" || exit

docker build -t mineru:latest .