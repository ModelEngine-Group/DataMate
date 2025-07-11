.PHONY: build-mineru build-datax build-data-juicer

build-mineru:
	sh build/mineru/build.sh

build-datax:
	sh build/datax/build.sh

build-data-juicer:
	sh build/data-juicer/build.sh

