# The data-juicer image includes all open-source contents of data-juicer,
# and it will be installed in editable mode.

FROM ubuntu:22.04

# change to aliyun source
RUN sed -i 's/archive.ubuntu.com/mirrors.huaweicloud.com/g' /etc/apt/sources.list && \
    sed -i 's/security.ubuntu.com/mirrors.huaweicloud.com/g' /etc/apt/sources.list

# install python 3.10
RUN DEBIAN_FRONTEND=noninteractive apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get install -y git curl vim wget python3.10 libpython3.10-dev python3-pip libgl1-mesa-glx libglib2.0-0 \
    && ln -sf /usr/bin/python3.10  /usr/bin/python3 \
    && ln -sf /usr/bin/python3.10  /usr/bin/python \
    && apt-get autoclean && rm -rf /var/lib/apt/lists/* \
    && pip install --upgrade pip -i https://mirrors.huaweicloud.com/repository/pypi/simple

# install 3rd-party system dependencies
RUN DEBIAN_FRONTEND=noninteractive apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get install -y ffmpeg libsm6 libxext6 software-properties-common build-essential cmake gfortran libopenblas-dev liblapack-dev postgresql postgresql-contrib libpq-dev

# prepare the java env
WORKDIR /opt
# download jdk
RUN wget https://aka.ms/download-jdk/microsoft-jdk-17.0.9-linux-x64.tar.gz -O jdk.tar.gz \
    && tar -xzf jdk.tar.gz \
    && rm -rf jdk.tar.gz \
    && mv jdk-17.0.9+8 jdk

# set the environment variable
ENV JAVA_HOME=/opt/jdk

# install uv
RUN pip install uv -i https://mirrors.huaweicloud.com/repository/pypi/simple

# install requirements which need to be installed from source
RUN uv pip install --upgrade setuptools==69.5.1 setuptools_scm -i https://mirrors.huaweicloud.com/repository/pypi/simple --system \
    && uv pip install http://dail-wlcb.oss-cn-wulanchabu.aliyuncs.com/data_juicer/recognize-anything-main.zip -i https://mirrors.huaweicloud.com/repository/pypi/simple --system

# install data-juicer then
RUN git clone https://github.com/modelscope/data-juicer.git

WORKDIR /data-juicer

RUN uv pip install -v -e .[all] -i https://mirrors.huaweicloud.com/repository/pypi/simple --system \
    && python -c "import nltk; nltk.download('punkt_tab'); nltk.download('punkt'); nltk.download('averaged_perceptron_tagger');  nltk.download('averaged_perceptron_tagger_eng')" \
    && pip cache purge