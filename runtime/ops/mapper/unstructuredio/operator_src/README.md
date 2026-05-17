# unstructuredio 算子源码

本目录是 DataMate 平台上传包中的算子源码。

## 功能

- 读取 DataMate 传入的 `filePath` 文件。
- 支持 PDF、DOCX、DOC 及 `unstructured` 可识别的其他文档格式。
- 输出 `unstructured` 风格 JSON。
- 核心字段包括 `index`、`category`、`text`、`page_number`、`coordinates`、`text_as_html`。

## 默认行为

- PDF 默认使用 `auto` 策略，尽量保持与 `unstructured` 原生输出一致。
- DOCX 默认启用兼容型快路径，失败时自动回退到 `unstructured` 原生解析。
- PDF 默认开启首页明显竖排乱码抑制，只过滤明显坏结果。
- 输出文件默认保存为 JSON。

## 注册关系

- `metadata.yml` 的 `raw_id` 为 `UnstructuredIOMapper`。
- `process.py` 中的类名为 `UnstructuredIOMapper`。
- `__init__.py` 注册路径为 `ops.user.unstructuredio.process`。
