# Image Processor Operator

A DataMate operator for processing images: classifying content and extracting text.

## Features

- **Content Classification**: Classify images as:
  - `document` - Text-heavy images
  - `screenshot` - Screen captures
  - `photo` - Natural photographs
  - `chart` - Charts and graphs
  - `qrcode` - QR codes and barcodes

- **OCR Text Extraction**: Extract text using Tesseract OCR
- **Confidence Scoring**: Get classification confidence
- **Metadata**: Image dimensions, format, size

## Input Parameters

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
    "image_info": {
        "width": 1920,
        "height": 1080,
        "format": "PNG",
        "size": 1024000
    }
}
```

## Usage

```python
from datamate import DataMate

operator = DataMate.load_operator("image_processor")
result = operator.process(
    image_path="/path/to/image.jpg",
    language="eng"
)
print(result)
```

## Requirements

- Python 3.8+
- pytesseract >= 0.3.10
- Pillow >= 9.0.0
- tesseract-ocr

## License

MIT
