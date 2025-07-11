#!/bin/bash

cd "$(dirname "$0")" || exit

git clone https://github.com/modelscope/data-juicer.git

docker build -t data-juicer:latest .

rm -rf data-juicer