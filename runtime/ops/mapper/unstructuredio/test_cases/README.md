# unstructuredio 测试用例

本目录提供 4 个公开样本文档测试用例，用于在 DataMate 平台验证 unstructuredio 算子的 PDF/DOCX 解析能力。测试输入文件统一放在 `example_input` 目录，当前保留 2 个公开 PDF 样本和 2 个公开 DOCX 样本。

## 样本来源

- Attention Is All You Need PDF: https://arxiv.org/pdf/1706.03762
- BERT PDF: https://arxiv.org/pdf/1810.04805
- DOCX 示例文档来源: https://file-examples.com/index.php/sample-documents-download/sample-doc-download/
- unstructured 开源项目: https://github.com/Unstructured-IO/unstructured

## 文件说明

- `cases.json`: 4 个平台测试 case，覆盖 PDF 文本、PDF 坐标、PDF 表格、DOCX 段落、DOCX 表格和 metadata 输出检查。
- `example_input/attention_is_all_you_need.pdf`: 公开论文 PDF 样本。
- `example_input/bert_pretraining.pdf`: 公开论文 PDF 样本。
- `example_input/docx_corpus_sample_1.docx`: 公开 DOCX 样本。
- `example_input/docx_corpus_sample_2.docx`: 公开 DOCX 样本。

## 测试方法

1. 在 DataMate 平台上传 unstructuredio 算子。
2. 选择 `example_input` 下的 PDF 或 DOCX 文件作为输入。
3. 参数保持默认即可；如需验证表格结构，保持 `pdfInferTableStructure=true`。
4. 执行后下载输出 JSON。
5. 检查输出是否包含非空 elements、正确文件类型、PDF 页码与坐标、DOCX 文本和 metadata 信息。

## 通过标准

- 输出文件为合法 JSON。
- `elements` 或等价结果数组非空。
- PDF 样本应保留 `page_number` 和 `coordinates`。
- DOCX 样本应保留段落、标题、表格等结构信息。
- 表格类元素应尽量保留 `Table` 类型或 `text_as_html` 字段。
