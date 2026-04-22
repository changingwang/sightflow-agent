"""
WhatsApp 驱动器 - 操作 WhatsApp Desktop
"""

import logging
import time
from typing import List, Optional, Tuple

from .base import BaseDriver, ChatInfo

logger = logging.getLogger(__name__)


class WhatsAppDriver(BaseDriver):
    """
    WhatsApp Desktop 驱动器
    
    通过视觉识别和模拟输入操作 WhatsApp。
    """
    
    name = "whatsapp"
    app_name = "whatsapp"
    
    # WhatsApp 窗口特征
    WINDOW_TITLE = "WhatsApp"
    
    # UI 区域（默认值）
    DEFAULT_CHAT_LIST_REGION = (0, 60, 350, 600)    # 左侧聊天列表
    DEFAULT_CHAT_REGION = (350, 60, 550, 500)       # 中间聊天区域
    DEFAULT_INPUT_REGION = (350, 560, 550, 100)     # 底部输入框
    
    def __init__(self):
        super().__init__()
        self.chat_list_region = self.DEFAULT_CHAT_LIST_REGION
        self.chat_region = self.DEFAULT_CHAT_REGION
        self.input_region = self.DEFAULT_INPUT_REGION
    
    def attach(self) -> bool:
        """附加到 WhatsApp"""
        logger.info("Attaching to WhatsApp...")
        
        window = self.find_window(self.WINDOW_TITLE)
        
        if window:
            self.window_handle = window
            self.bring_to_front()
            time.sleep(0.5)
            
            self.attached = True
            logger.info("Attached to WhatsApp successfully")
            return True
        
        logger.warning("WhatsApp window not found.")
        return False
    
    def open_chat(self, contact: str) -> bool:
        """打开聊天"""
        if not self.attached:
            if not self.attach():
                return False
        
        logger.info(f"Opening chat with: {contact}")
        
        # 使用搜索
        if self._search_and_open(contact):
            return True
        
        return False
    
    def type_message(self, text: str):
        """输入消息"""
        if not self.input_region:
            return
        
        x = self.input_region[0] + 50
        y = self.input_region[1] + 40
        self.click(x, y)
        
        time.sleep(0.2)
        
        import pyautogui
        pyautogui.write(text, interval=0.05)
    
    def send(self):
        """发送消息"""
        self.press_key("enter")
    
    def get_chat_list(self) -> List[ChatInfo]:
        """获取聊天列表"""
        return []
    
    def _search_and_open(self, contact: str) -> bool:
        """通过搜索打开聊天"""
        try:
            import pyautogui
            
            # Ctrl+F 搜索
            self.hotkey("ctrl", "f")
            time.sleep(0.3)
            
            pyautogui.write(contact, interval=0.1)
            time.sleep(0.5)
            
            self.press_key("enter")
            time.sleep(0.3)
            
            return True
            
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return False
