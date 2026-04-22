"""
SightFlow Agent - 视觉驱动的通用 IM Agent

让 AI 像人一样操作微信/WhatsApp，零封号风险！
"""

__version__ = "0.1.0"
__author__ = "大豆 <soad666p>"
__license__ = "MIT"

from .agent import VisionAgent
from .scanner import ScreenScanner
from .drivers import WeChatDriver, WhatsAppDriver
from .ocr import OCR

__all__ = [
    "VisionAgent",
    "ScreenScanner",
    "WeChatDriver",
    "WhatsAppDriver",
    "OCR",
]
