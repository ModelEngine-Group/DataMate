# Image OCR Extractor Operator

A DataMate operator for extracting text from images using OCR.

## Features

- **Content Classification**: document, screenshot, photo, chart, qrcode
- **OCR Text Extraction**: Extract text using Tesseract
- **Confidence Scoring**: Get classification confidence
- **Metadata**: Image dimensions, format, size

## Input

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| image_path | string | Yes | Path or URL to image |
| language | string | No | OCR language (default: eng) |

## Output

```python
{
    "category": "document",
    "text": "Extracted text...",
    "confidence": 0.95,
    "image_info": {"width": 1920, "height": 1080, "format": "PNG", "size": 1024000}
}
```

## Usage

```python
from datamate import DataMate

operator = DataMate.load_operator("image_ocr_extractor")
result = operator.process(image_path="/path/to/image.jpg")
print(result)
```

## Requirements

- Python 3.8+
- pytesseract >= 0.3.10
- Pillow >= 9.0.0
- tesseract-ocr

## License

MIT
