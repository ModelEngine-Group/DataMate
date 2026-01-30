FROM ghcr.io/astral-sh/uv:python3.11-bookworm AS opencv-builder

RUN apt-get update \
    && apt-get install build-essential cmake git pkg-config python3-dev python3-numpy libjpeg-dev libpng-dev \
    libtiff-dev libopenblas-dev liblapack-dev -y

RUN mkdir -p /opt/opencv && \
    cd /opt/opencv && \
    git clone https://github.com/opencv/opencv.git && \
    git clone https://github.com/opencv/opencv_contrib.git && \
    cd opencv && \
    mkdir build && \
    cd build && \
    cmake -D CMAKE_BUILD_TYPE=RELEASE \
      -D CMAKE_INSTALL_PREFIX=/usr/local/opencv \
      -D OPENCV_EXTRA_MODULES_PATH=../../opencv_contrib/modules \
      -D CMAKE_CXX_FLAGS="-march=armv8-a" \
      -D WITH_OPENMP=ON \
      -D ENABLE_NEON=ON \
      -D WITH_TBB=OFF \
      -D BUILD_opencv_python3=ON \
      .. \
    && make -j$(nproc) \
    && make install \
    && ldconfig

FROM ghcr.io/astral-sh/uv:python3.11-bookworm

RUN --mount=type=cache,target=/var/cache/apt \
    --mount=type=cache,target=/var/lib/apt \
    apt update \
    && apt install -y libgl1 libglib2.0-0 vim libmagic1 libreoffice dos2unix swig poppler-utils tesseract-ocr libgomp1 \
    libopenblas0 libjpeg62-turbo libpng16-16 libtiff6 libwebp7 libopenjp2-7

RUN mkdir -p /home/models \
    && wget https://paddle-model-ecology.bj.bcebos.com/paddlex/official_inference_model/paddle3.0.0/PP-LCNet_x1_0_doc_ori_infer.tar \
    && tar -xf PP-LCNet_x1_0_doc_ori_infer.tar -C /home/models \
    && rm -f PP-*.tar

COPY runtime/python-executor /opt/runtime
COPY runtime/ops /opt/runtime/datamate/ops
COPY runtime/ops/user /opt/runtime/user
COPY scripts/images/runtime/start.sh /opt/runtime/start.sh

ENV PYTHONPATH=/opt/runtime/datamate/
ENV UV_EXTRA_INDEX_URL="https://download.pytorch.org/whl/cpu"
ENV UV_INDEX_STRATEGY=unsafe-best-match

WORKDIR /opt/runtime

RUN --mount=type=cache,target=/root/.cache/uv \
    uv pip install -e ".[extra]" --system \
    && uv pip install -r /opt/runtime/datamate/ops/pyproject.toml --extra extra --system \
    && python -m spacy download zh_core_web_sm \
    && python -c "import nltk; nltk.download('punkt_tab'); nltk.download('averaged_perceptron_tagger_eng')" \
    && echo "/usr/local/lib/ops/site-packages" > /usr/local/lib/python3.11/site-packages/ops.pth

RUN pip uninstall opencv-python opencv-contrib-python opencv-python-headless opencv-contrib-python-headless -y

COPY --from=opencv-builder /usr/local/opencv /usr/local/

RUN mkdir -p /usr/share/fonts/truetype/custom && \
    wget -O /usr/share/fonts/truetype/custom/FangSong_GB2312.ttf https://github.com/XiangyunHuang/fonts/raw/master/FangSong_GB2312.ttf

RUN ln -sf /usr/share/zoneinfo/Asia/Shanghai /etc/localtime \
    && chmod +x /opt/runtime/start.sh \
    && dos2unix /opt/runtime/start.sh

EXPOSE 8081

ENTRYPOINT ["/opt/runtime/start.sh"]
