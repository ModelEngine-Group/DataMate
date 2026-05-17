# unstructuredio 测试用例

本目录提供公开可下载的 PDF 和 DOCX 样本，用于验收平台复测文档解析算子。

## 公开样本来源

- `example_input/attention_is_all_you_need.pdf`
  arXiv 论文 *Attention Is All You Need*：
  <https://arxiv.org/pdf/1706.03762.pdf>
- `example_input/bert_pretraining.pdf`
  arXiv 论文 *BERT: Pre-training of Deep Bidirectional Transformers for Language Understanding*：
  <https://arxiv.org/pdf/1810.04805.pdf>
- `example_input/docx_corpus_sample_1.docx`
  公开 `docx-corpus` 样本：
  <https://docxcorp.us/>
  <https://docxcorp.us/documents/00042714bec87fe8097f604fdd230760c956aac77fa56fcd5bc5ffb68c60690a.docx>
- `example_input/docx_corpus_sample_2.docx`
  公开 `docx-corpus` 样本：
  <https://docxcorp.us/>
  <https://docxcorp.us/documents/000e366a02330e96ce5e878a2c2ecceba7374715a1065a5ece914d024a25d951.docx>

## 平台测试步骤

1. 在 DataMate 算子市场上传 `../unstructuredio.zip`。
2. 创建任务并上传 `example_input/` 下任一 PDF 或 DOCX 文件。
3. 对 PDF 样本建议使用默认 `pdfStrategy=auto` 和 `pdfInferTableStructure=true`。
4. 运行任务并下载输出 JSON。

## 检查项

- 输出文件非空，JSON 可解析。
- 元素至少包含 `category`、`text`、`page_number`、`coordinates` 字段。
- PDF 输出的 `page_number` 不应全部为 `1`。
- PDF 标题、正文、表格标题附近文本应可读。
- DOCX 输出的标题、段落、表格顺序应基本合理。
- DOCX 的 `coordinates` 不应全部为空。
