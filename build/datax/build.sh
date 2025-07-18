#!/bin/bash

cd "$(dirname "$0")" || exit

cp -r ../../extensions/datax .

docker build -t datax:latest .

rm -rf datax