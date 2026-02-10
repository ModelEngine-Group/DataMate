"""
Image Extractor Operator

A DataMate operator for extracting text from images and classifying content.
"""

import os
from typing import Any, Dict, Optional
from urllib.parse import urlparse
from urllib.request import urlopen

import pytesseract
from PIL import Image


class ImageExtractorOperator:
    """
    Operator for extracting text from images and classifying content.
    
    Features:
    - Classify images (document, screenshot, photo, chart, qrcode)
    - Extract text using Tesseract OCR
    - Provide confidence scores
    - Return image metadata
    """
    
    CATEGORY_PATTERNS = {
        "document": {"min_ar": 0.5, "max_ar": 2.0, "min_res": (300, 300)},
        "screenshot": {"min_ar": 0.8, "max_ar": 2.5, "min_res": (100, 100)},
        "photo": {"min_ar": 0.3, "max_ar": 3.0, "min_res": (200, 200)},
        "chart": {"min_ar": 0.5, "max_ar": 2.0, "min_res": (200, 200)},
        "qrcode": {"min_ar": 0.9, "max_ar": 1.1, "min_res": (100, 100)}
    }
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.default_language = self.config.get("language", "eng")
    
    def process(self, image_path: str, language: str = None) -> Dict[str, Any]:
        """Extract text and classify image."""
        language = language or self.default_language
        
        image = self._load_image(image_path)
        info = self._get_image_info(image)
        category, confidence = self._classify_image(image)
        text = self._extract_text(image, language)
        
        return {
            "category": category,
            "text": text,
            "confidence": confidence,
            "image_info": info
        }
    
    def _load_image(self, path: str) -> Image.Image:
        if self._is_url(path):
            with urlopen(path) as r:
                return Image.open(r)
        return Image.open(path)
    
    def _is_url(self, path: str) -> bool:
        try:
            return urlparse(path).scheme in ("http", "https")
        except:
            return False
    
    def _get_image_info(self, image: Image.Image) -> Dict[str, Any]:
        return {
            "width": image.width,
            "height": image.height,
            "format": image.format,
            "size": os.path.getsize(image.filename) if image.filename else 0
        }
    
    def _classify_image(self, image: Image.Image) -> tuple[str, float]:
        ar = image.width / image.height
        scores = {}
        
        for cat, pat in self.CATEGORY_PATTERNS.items():
            score = 0.0
            if pat["min_ar"] <= ar <= pat["max_ar"]:
                score += 0.5
            if image.width >= pat["min_res"][0] and image.height >= pat["min_res"][1]:
                score += 0.3
            if cat == "qrcode" and 0.95 <= ar <= 1.05:
                score += 0.5
            if cat == "document":
                try:
                    if len(pytesseract.image_to_string(image, timeout=2).strip()) > 50:
                        score += 0.4
                except:
                    pass
            scores[cat] = min(score, 1.0)
        
        if scores:
            best = max(scores, key=scores.get)
            confidence = scores[best]
            if confidence >= 0.3:
                return best, confidence
            return "photo", 0.5
        return "photo", 0.5
    
    def _extract_text(self, image: Image.Image, language: str) -> str:
        try:
            return pytesseract.image_to_string(image, lang=language).strip()
        except Exception as e:
            return f"Error: {str(e)}"


def run(image_path: str, language: str = "eng") -> Dict[str, Any]:
    """Convenience function."""
    return ImageExtractorOperator().process(image_path, language)
