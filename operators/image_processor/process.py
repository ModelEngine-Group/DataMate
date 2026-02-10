"""
Image Processor Operator

A DataMate operator for processing images: classifying content and extracting text.
"""

import os
from typing import Any, Dict, Optional
from urllib.parse import urlparse
from urllib.request import urlopen

import pytesseract
from PIL import Image


class ImageProcessorOperator:
    """
    Operator for processing images: classification and OCR text extraction.
    
    Features:
    - Classify images (document, screenshot, photo, chart, qrcode)
    - Extract text using Tesseract OCR
    - Provide confidence scores
    - Return image metadata
    """
    
    CATEGORY_PATTERNS = {
        "document": {
            "min_aspect_ratio": 0.5,
            "max_aspect_ratio": 2.0,
            "min_resolution": (300, 300),
        },
        "screenshot": {
            "min_aspect_ratio": 0.8,
            "max_aspect_ratio": 2.5,
            "min_resolution": (100, 100),
        },
        "photo": {
            "min_aspect_ratio": 0.3,
            "max_aspect_ratio": 3.0,
            "min_resolution": (200, 200),
        },
        "chart": {
            "min_aspect_ratio": 0.5,
            "max_aspect_ratio": 2.0,
            "min_resolution": (200, 200),
        },
        "qrcode": {
            "min_aspect_ratio": 0.9,
            "max_aspect_ratio": 1.1,
            "min_resolution": (100, 100),
        }
    }
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """Initialize the Image Processor operator."""
        self.config = config or {}
        self.default_language = self.config.get("language", "eng")
    
    def process(self, image_path: str, language: Optional[str] = None) -> Dict[str, Any]:
        """
        Process image: classify content and extract text.
        
        Args:
            image_path: Path or URL to the image
            language: OCR language code
            
        Returns:
            Dictionary with category, text, confidence, and image_info
        """
        language = language or self.default_language
        
        image = self._load_image(image_path)
        image_info = self._get_image_info(image)
        category, confidence = self._classify_image(image)
        text = self._extract_text(image, language)
        
        return {
            "category": category,
            "text": text,
            "confidence": confidence,
            "image_info": image_info
        }
    
    def _load_image(self, image_path: str) -> Image.Image:
        """Load image from file path or URL."""
        if self._is_url(image_path):
            with urlopen(image_path) as response:
                return Image.open(response)
        return Image.open(image_path)
    
    def _is_url(self, path: str) -> bool:
        """Check if path is a URL."""
        try:
            result = urlparse(path)
            return result.scheme in ("http", "https")
        except Exception:
            return False
    
    def _get_image_info(self, image: Image.Image) -> Dict[str, Any]:
        """Get image metadata."""
        return {
            "width": image.width,
            "height": image.height,
            "format": image.format,
            "size": os.path.getsize(image.filename) if image.filename else 0
        }
    
    def _classify_image(self, image: Image.Image) -> tuple[str, float]:
        """Classify image into a category."""
        width, height = image.width, image.height
        aspect_ratio = width / height
        
        scores = {}
        
        for category, pattern in self.CATEGORY_PATTERNS.items():
            score = 0.0
            
            if pattern["min_aspect_ratio"] <= aspect_ratio <= pattern["max_aspect_ratio"]:
                score += 0.5
            
            if width >= pattern["min_resolution"][0] and height >= pattern["min_resolution"][1]:
                score += 0.3
            
            if category == "qrcode" and 0.95 <= aspect_ratio <= 1.05:
                score += 0.5
            
            if category == "document":
                try:
                    text = pytesseract.image_to_string(image, timeout=2)
                    if len(text.strip()) > 50:
                        score += 0.4
                except Exception:
                    pass
            
            scores[category] = min(score, 1.0)
        
        if scores:
            best_category = max(scores, key=scores.get)
            best_score = scores[best_category]
            
            if best_score < 0.3:
                return "photo", 0.5
            
            return best_category, best_score
        
        return "photo", 0.5
    
    def _extract_text(self, image: Image.Image, language: str) -> str:
        """Extract text from image using OCR."""
        try:
            text = pytesseract.image_to_string(image, lang=language)
            return text.strip()
        except pytesseract.TesseractError as e:
            return f"OCR Error: {str(e)}"
        except Exception as e:
            return f"Error: {str(e)}"


def run(image_path: str, language: str = "eng") -> Dict[str, Any]:
    """Convenience function to process image."""
    operator = ImageProcessorOperator()
    return operator.process(image_path, language)
