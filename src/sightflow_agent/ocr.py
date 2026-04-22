"""
OCR 文字识别 - 从屏幕截图中提取文字
"""

import logging
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class OCR:
    """
    OCR 文字识别
    
    支持多种 OCR 引擎：
    - Tesseract (本地，免费)
    - PaddleOCR (中文优化)
    - EasyOCR (多语言)
    """
    
    def __init__(self, engine: str = "auto", lang: str = "zh+en"):
        """
        初始化 OCR
        
        Args:
            engine: OCR 引擎 (auto/tesseract/paddle/easyocr)
            lang: 识别语言 (zh+en 表示中英文混合)
        """
        self.engine_name = engine
        self.lang = lang
        self._engine = None
        
        self._init_engine()
    
    def _init_engine(self):
        """初始化 OCR 引擎"""
        if self.engine_name == "auto":
            # 自动选择最佳引擎
            self._engine = self._init_best_available()
        elif self.engine_name == "tesseract":
            self._engine = self._init_tesseract()
        elif self.engine_name == "paddle":
            self._engine = self._init_paddle()
        elif self.engine_name == "easyocr":
            self._engine = self._init_easyocr()
        
        if self._engine is None:
            logger.warning("No OCR engine available. Install: pip install paddleocr")
    
    def _init_best_available(self):
        """初始化最佳可用引擎"""
        # 优先级：PaddleOCR > EasyOCR > Tesseract
        try:
            return self._init_paddle()
        except ImportError:
            pass
        
        try:
            return self._init_easyocr()
        except ImportError:
            pass
        
        try:
            return self._init_tesseract()
        except ImportError:
            pass
        
        return None
    
    def _init_paddle(self):
        """初始化 PaddleOCR"""
        try:
            from paddleocr import PaddleOCR
            ocr = PaddleOCR(
                use_angle_cls=True,
                lang='ch',
                show_log=False,
            )
            logger.info("PaddleOCR initialized")
            return ocr
        except ImportError:
            logger.debug("PaddleOCR not installed")
            return None
    
    def _init_easyocr(self):
        """初始化 EasyOCR"""
        try:
            import easyocr
            reader = easyocr.Reader(['ch_sim', 'en'], gpu=False)
            logger.info("EasyOCR initialized")
            return reader
        except ImportError:
            logger.debug("EasyOCR not installed")
            return None
    
    def _init_tesseract(self):
        """初始化 Tesseract"""
        try:
            import pytesseract
            logger.info("Tesseract initialized")
            return pytesseract
        except ImportError:
            logger.debug("Tesseract not installed")
            return None
    
    def recognize(self, image, region: Optional[Tuple[int, int, int, int]] = None) -> str:
        """
        识别文字
        
        Args:
            image: PIL Image 或 图片路径
            region: 识别区域 (x, y, width, height)
        
        Returns:
            识别的文字
        """
        if self._engine is None:
            return ""
        
        # 裁剪区域
        if region:
            from PIL import Image
            if isinstance(image, Image.Image):
                image = image.crop(region)
        
        # 识别
        try:
            if hasattr(self._engine, 'ocr'):
                # PaddleOCR
                result = self._engine.ocr(image)
                text = " ".join([line[1][0] for line in result[0]] if result[0] else [])
            
            elif hasattr(self._engine, 'readtext'):
                # EasyOCR
                result = self._engine.readtext(image)
                text = " ".join([r[1] for r in result])
            
            elif hasattr(self._engine, 'image_to_string'):
                # Tesseract
                text = self._engine.image_to_string(image, lang='chi_sim+eng')
            
            else:
                text = ""
            
            logger.debug(f"OCR recognized: {text[:50]}...")
            return text.strip()
            
        except Exception as e:
            logger.error(f"OCR error: {e}")
            return ""
    
    def extract_text_regions(self, image) -> List[Tuple[int, int, int, int]]:
        """
        提取文字区域
        
        Returns:
            文字区域列表 [(x, y, w, h), ...]
        """
        if self._engine is None:
            return []
        
        try:
            if hasattr(self._engine, 'ocr'):
                # PaddleOCR
                result = self._engine.ocr(image)
                regions = []
                for line in result[0]:
                    box = line[0]
                    x, y = int(min(p[0] for p in box)), int(min(p[1] for p in box))
                    w = int(max(p[0] for p in box) - x)
                    h = int(max(p[1] for p in box) - y)
                    regions.append((x, y, w, h))
                return regions
            
            elif hasattr(self._engine, 'readtext'):
                # EasyOCR
                result = self._engine.readtext(image)
                regions = []
                for box, text, conf in result:
                    x, y = int(min(p[0] for p in box)), int(min(p[1] for p in box))
                    w = int(max(p[0] for p in box) - x)
                    h = int(max(p[1] for p in box) - y)
                    regions.append((x, y, w, h))
                return regions
            
        except Exception as e:
            logger.error(f"Extract regions error: {e}")
        
        return []
    
    def detect_language(self, text: str) -> str:
        """
        检测文字语言
        
        Returns:
            语言代码 (zh/en/unknown)
        """
        import re
        
        # 检测中文字符
        if re.search(r'[\u4e00-\u9fff]', text):
            return "zh"
        
        # 检测英文
        if re.search(r'[a-zA-Z]', text):
            return "en"
        
        return "unknown"
