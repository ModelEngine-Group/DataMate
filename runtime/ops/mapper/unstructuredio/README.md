# unstructuredio 算子

## 目录内容

-   `operator_src/` DataMate 算子源码。
-   `test_cases/` 公开 PDF 和 DOCX 测试样本及测试说明。
-   `README.md` 本说明文件。

## 开源模型链接

-   版面检测模型 `unstructuredio/yolo_x_layout`： [https://huggingface.co/unstructuredio/yolo\_x\_layout](https://huggingface.co/unstructuredio/yolo_x_layout "https://huggingface.co/unstructuredio/yolo_x_layout")
-   表格结构识别模型 `microsoft/table-transformer-structure-recognition`： [https://huggingface.co/microsoft/table-transformer-structure-recognition](https://huggingface.co/microsoft/table-transformer-structure-recognition "https://huggingface.co/microsoft/table-transformer-structure-recognition")
-   `YOLOX` 上游开源项目： [https://github.com/Megvii-BaseDetection/YOLOX](https://github.com/Megvii-BaseDetection/YOLOX "https://github.com/Megvii-BaseDetection/YOLOX")

## 路径和模型配置

算子代码默认使用容器内模型路径：

-   `UNSTRUCTUREDIO_LAYOUT_MODEL_PATH=/models/unstructuredio/yolo_x_layout/yolox_l0.05.onnx`
-   `UNSTRUCTUREDIO_TABLE_MODEL_PATH=/models/unstructuredio/table-transformer-structure-recognition`

`/models` 是容器内约定挂载点。可把本机任意模型目录挂载到容器内 `/models`，或通过上述环境变量改成其他容器内路径。

## 如何生成 DataMate 上传包

建议生成的上传包文件名为 `unstructuredio.zip`。

方式一：如果平台接受压缩包根目录直接包含算子文件，则压缩 `operator_src/` 目录中的全部文件。

方式二：如果平台要求压缩包内有顶层算子目录，则新建临时目录 `unstructuredio/`，将 `operator_src/` 中的以下文件放入该目录后压缩：

-   `metadata.yml`
-   `process.py`
-   `__init__.py`
-   `requirements.txt`
-   `README.md`

不要把 `test_cases/` 放入 DataMate 算子上传包。

## 平台测试

1.  在 DataMate 算子市场上传按上述规则生成的上传包。
2.  新建数据处理任务，选择 `unstructuredio` 算子。
3.  上传 `test_cases/example_input/` 下的 PDF 或 DOCX 样本。
4.  运行任务并下载输出 JSON。
5.  按 `test_cases/README.md` 中的检查项确认输出结构、页码、坐标和表格字段。