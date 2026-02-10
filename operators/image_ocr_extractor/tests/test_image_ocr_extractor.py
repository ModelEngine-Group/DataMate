"""
Test cases for ImageOCRExtractorOperator
"""

import os
import pytest
from unittest.mock import Mock, patch
from PIL import Image
import io
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from process import ImageOCRExtractorOperator


class TestImageOCRExtractorOperator:
    """Test suite for ImageOCRExtractorOperator."""
    
    @pytest.fixture
    def operator(self):
        """Create operator instance."""
        return ImageOCRExtractorOperator()
    
    @pytest.fixture
    def sample_image(self, tmp_path):
        """Create a sample test image."""
        img = Image.new('RGB', (800, 600), color='white')
        path = tmp_path / "test_image.png"
        img.save(path)
        return str(path)
    
    @pytest.fixture
    def text_image(self, tmp_path):
        """Create an image with text-like patterns."""
        img = Image.new('RGB', (400, 400), color='lightgray')
        path = tmp_path / "text_image.png"
        img.save(path)
        return str(path)
    
    def test_operator_initialization(self, operator):
        """Test operator can be initialized with default config."""
        assert operator is not None
        assert operator.default_language == "eng"
    
    def test_operator_initialization_with_config(self):
        """Test operator initialization with custom config."""
        config = {"language": "chi_sim"}
        operator = ImageOCRExtractorOperator(config)
        assert operator.default_language == "chi_sim"
    
    def test_classification_patterns_exist(self, operator):
        """Test that CATEGORY_PATTERNS contains expected categories."""
        expected_categories = ["document", "screenshot", "photo", "chart", "qrcode"]
        for cat in expected_categories:
            assert cat in operator.CATEGORY_PATTERNS
    
    def test_load_local_image(self, operator, sample_image):
        """Test loading a local image file."""
        image = operator._load_image(sample_image)
        assert image is not None
        assert isinstance(image, Image.Image)
    
    def test_get_image_info(self, operator, sample_image):
        """Test extracting image metadata."""
        image = operator._load_image(sample_image)
        info = operator._get_image_info(image)
        
        assert "width" in info
        assert "height" in info
        assert "format" in info
        assert "size" in info
        assert info["width"] == 800
        assert info["height"] == 600
    
    def test_is_url_detection(self, operator):
        """Test URL detection logic."""
        assert operator._is_url("http://example.com/image.png") is True
        assert operator._is_url("https://example.com/image.png") is True
        assert operator._is_url("/path/to/image.png") is False
        assert operator._is_url("image.png") is False
    
    @patch('process.urlopen')
    def test_load_remote_image(self, mock_urlopen, operator):
        """Test loading image from URL."""
        mock_response = Mock()
        mock_response.__enter__ = Mock(return_value=mock_response)
        mock_response.__exit__ = Mock(return_value=False)
        mock_response.read.return_value = b''
        mock_response.headers = {'content-type': 'image/png'}
        mock_response.url = 'http://example.com/test.png'
        mock_urlopen.return_value = mock_response
        
        with patch('PIL.Image.open') as mock_image_open:
            mock_img = Mock(spec=Image.Image)
            mock_image_open.return_value = mock_img
            
            result = operator._load_image("http://example.com/image.png")
            assert result is not None
    
    def test_classify_image_aspect_ratio(self, operator, tmp_path):
        """Test image classification based on aspect ratio."""
        # Square image (potential QR code)
        square_img = Image.new('RGB', (100, 100), color='white')
        square_path = tmp_path / "square.png"
        square_img.save(square_path)
        
        image = operator._load_image(str(square_path))
        result = operator._classify_image(image)
        
        assert isinstance(result, tuple)
        category, confidence = result
        assert category in ["qrcode", "photo", "screenshot"]
        assert 0 <= confidence <= 1
    
    def test_classify_wide_image(self, operator, tmp_path):
        """Test classification of wide aspect ratio image."""
        wide_img = Image.new('RGB', (800, 300), color='white')
        wide_path = tmp_path / "wide.png"
        wide_img.save(wide_path)
        
        image = operator._load_image(str(wide_path))
        result = operator._classify_image(image)
        
        assert isinstance(result, tuple)
        category, confidence = result
        assert category in ["screenshot", "photo", "document"]
        assert 0 <= confidence <= 1
    
    def test_classify_tall_image(self, operator, tmp_path):
        """Test classification of tall aspect ratio image."""
        tall_img = Image.new('RGB', (300, 800), color='white')
        tall_path = tmp_path / "tall.png"
        tall_img.save(tall_path)
        
        image = operator._load_image(str(tall_path))
        result = operator._classify_image(image)
        
        assert isinstance(result, tuple)
        category, confidence = result
        assert category in ["photo", "document"]
        assert 0 <= confidence <= 1
    
    def test_process_returns_dict(self, operator, sample_image):
        """Test that process method returns expected dictionary structure."""
        with patch('process.pytesseract.image_to_string') as mock_ocr:
            mock_ocr.return_value = "Test text"
            
            result = operator.process(sample_image)
            
            assert isinstance(result, dict)
            assert "category" in result
            assert "text" in result
            assert "confidence" in result
            assert "image_info" in result
    
    def test_process_with_custom_language(self, operator, sample_image):
        """Test process method with custom language parameter."""
        with patch('process.pytesseract.image_to_string') as mock_ocr:
            mock_ocr.return_value = "Test text"
            
            result = operator.process(sample_image, language="chi_sim")
            
            assert result["category"] is not None
            assert "text" in result
            assert result["image_info"]["width"] == 800
    
    def test_text_extraction_with_mock(self, operator, sample_image):
        """Test text extraction functionality."""
        with patch('process.pytesseract.image_to_string') as mock_ocr:
            mock_ocr.return_value = "Sample extracted text"
            
            image = operator._load_image(sample_image)
            text = operator._extract_text(image, "eng")
            
            assert text == "Sample extracted text"
            mock_ocr.assert_called_once()
    
    def test_text_extraction_error_handling(self, operator, sample_image):
        """Test error handling in text extraction."""
        with patch('process.pytesseract.image_to_string') as mock_ocr:
            mock_ocr.side_effect = Exception("OCR failed")
            
            image = operator._load_image(sample_image)
            text = operator._extract_text(image, "eng")
            
            assert "Error:" in text
    
    def test_convenience_run_function(self):
        """Test the convenience run function."""
        from process import run
        
        with patch.object(ImageOCRExtractorOperator, 'process') as mock_process:
            mock_process.return_value = {
                "category": "document",
                "text": "test",
                "confidence": 0.8,
                "image_info": {}
            }
            
            result = run("test_image.png", "eng")
            
            assert isinstance(result, dict)
            assert result["category"] == "document"
    
    def test_category_pattern_structure(self, operator):
        """Test that all category patterns have required fields."""
        required_fields = ["min_ar", "max_ar", "min_res"]
        
        for category, pattern in operator.CATEGORY_PATTERNS.items():
            for field in required_fields:
                assert field in pattern, f"Missing {field} in {category}"
    
    def test_image_info_returns_integers(self, operator, sample_image):
        """Test that image_info returns proper numeric types."""
        image = operator._load_image(sample_image)
        info = operator._get_image_info(image)
        
        assert isinstance(info["width"], int)
        assert isinstance(info["height"], int)
        assert isinstance(info["size"], int)
    
    def test_process_full_workflow(self, operator, tmp_path):
        """Test complete processing workflow with mocked OCR."""
        img = Image.new('RGB', (640, 480), color='blue')
        path = tmp_path / "test.png"
        img.save(path)
        
        with patch('process.pytesseract.image_to_string') as mock_ocr:
            mock_ocr.return_value = "Hello World 123"
            
            result = operator.process(str(path), language="eng")
            
            assert "category" in result
            assert "text" in result
            assert "confidence" in result
            assert "image_info" in result
            assert result["image_info"]["width"] == 640
            assert result["image_info"]["height"] == 480
    
    def test_qrcode_classification(self, operator, tmp_path):
        """Test QR code specific classification."""
        qr_img = Image.new('RGB', (100, 100), color='white')
        qr_path = tmp_path / "qrcode.png"
        qr_img.save(qr_path)
        
        image = operator._load_image(str(qr_path))
        category, confidence = operator._classify_image(image)
        
        # Square images should score high on qrcode
        assert category == "qrcode"
        assert confidence >= 0.5
    
    def test_document_classification_with_text(self, operator, tmp_path):
        """Test document classification when OCR detects text."""
        doc_img = Image.new('RGB', (500, 700), color='white')
        doc_path = tmp_path / "document.png"
        doc_img.save(doc_path)
        
        with patch('process.pytesseract.image_to_string') as mock_ocr:
            mock_ocr.return_value = "This is a long document text with multiple lines of content."
            
            image = operator._load_image(str(doc_path))
            category, confidence = operator._classify_image(image)
            
            assert category == "document"
            assert confidence > 0.5


class TestImageOCRExtractorEdgeCases:
    """Test edge cases for ImageOCRExtractorOperator."""
    
    @pytest.fixture
    def operator(self):
        return ImageOCRExtractorOperator()
    
    def test_invalid_image_path(self, operator):
        """Test handling of invalid image path."""
        with pytest.raises(FileNotFoundError):
            operator.process("/nonexistent/path/image.png")
    
    def test_empty_language_defaults_to_config(self, operator, tmp_path):
        """Test that empty language uses config default."""
        img = Image.new('RGB', (100, 100), color='white')
        path = tmp_path / "test.png"
        img.save(path)
        
        with patch('process.pytesseract.image_to_string') as mock_ocr:
            mock_ocr.return_value = ""
            
            result = operator.process(str(path), language="")
            mock_ocr.assert_called()
    
    def test_confidence_score_range(self, operator, tmp_path):
        """Test that confidence scores are within valid range."""
        img = Image.new('RGB', (400, 400), color='white')
        path = tmp_path / "test.png"
        img.save(path)
        
        image = operator._load_image(str(path))
        result = operator._classify_image(image)
        
        assert isinstance(result, tuple)
        category, confidence = result
        assert 0 <= confidence <= 1
    
    def test_various_image_formats(self, operator, tmp_path):
        """Test handling of various image characteristics."""
        test_cases = [
            ((100, 100), "Square image"),
            ((800, 600), "Landscape image"),
            ((600, 800), "Portrait image"),
            ((1920, 1080), "Wide resolution"),
        ]
        
        with patch('process.pytesseract.image_to_string') as mock_ocr:
            mock_ocr.return_value = "Test"
            
            for (width, height), desc in test_cases:
                img = Image.new('RGB', (width, height), color='gray')
                path = tmp_path / f"test_{width}x{height}.png"
                img.save(path)
                
                result = operator.process(str(path))
                
                assert "category" in result, f"Failed for {desc}"
                assert "image_info" in result, f"Failed for {desc}"
                assert result["image_info"]["width"] == width, f"Failed for {desc}"
                assert result["image_info"]["height"] == height, f"Failed for {desc}"
    
    def test_ocr_language_parameter(self, operator, tmp_path):
        """Test that OCR language parameter is passed correctly."""
        img = Image.new('RGB', (100, 100), color='white')
        path = tmp_path / "test.png"
        img.save(path)
        
        with patch('process.pytesseract.image_to_string') as mock_ocr:
            mock_ocr.return_value = "Text"
            
            operator.process(str(path), language="chi_sim")
            
            call_args = mock_ocr.call_args
            assert "chi_sim" in str(call_args) or call_args[1].get('lang') == "chi_sim"
    
    def test_classify_image_consistency(self, operator, tmp_path):
        """Test that classification returns consistent types."""
        img = Image.new('RGB', (500, 500), color='white')
        path = tmp_path / "test.png"
        img.save(path)
        
        image = operator._load_image(str(path))
        results = [operator._classify_image(image) for _ in range(3)]
        
        types = [type(r) for r in results]
        assert all(t == types[0] for t in types), "Inconsistent return types"
    
    def test_metadata_integration(self):
        """Test operator metadata structure."""
        import yaml
        
        metadata_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "metadata.yml"
        )
        
        with open(metadata_path) as f:
            metadata = yaml.safe_load(f)
        
        assert metadata["name"] == "image_ocr_extractor"
        assert "input_schema" in metadata
        assert "output_schema" in metadata
        assert "requirements" in metadata


class TestImageOCRExtractorIntegration:
    """Integration tests for ImageOCRExtractorOperator."""
    
    def test_operator_import(self):
        """Test that operator can be imported correctly."""
        from process import ImageOCRExtractorOperator, run
        assert ImageOCRExtractorOperator is not None
        assert callable(run)
    
    def test_operator_instantiation(self):
        """Test operator instantiation."""
        op = ImageOCRExtractorOperator()
        assert hasattr(op, 'process')
        assert hasattr(op, '_load_image')
        assert hasattr(op, '_classify_image')
        assert hasattr(op, '_extract_text')
    
    def test_config_persistence(self):
        """Test that config is persisted correctly."""
        config = {"language": "deu", "custom_option": True}
        operator = ImageOCRExtractorOperator(config)
        
        assert operator.config == config
        assert operator.default_language == "deu"
    
    def test_all_methods_exist(self):
        """Test all required methods exist."""
        operator = ImageOCRExtractorOperator()
        
        required_methods = [
            'process', '_load_image', '_is_url', 
            '_get_image_info', '_classify_image', '_extract_text'
        ]
        
        for method in required_methods:
            assert hasattr(operator, method), f"Missing method: {method}"
            assert callable(getattr(operator, method)), f"Not callable: {method}"
