"""
IM 驱动器基础类
"""

import logging
from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class ChatInfo:
    """聊天信息"""
    name: str
    last_message: str
    unread_count: int
    position: Tuple[int, int, int, int]


class BaseDriver(ABC):
    """
    IM 驱动器基类
    
    负责与具体 IM 应用交互。
    """
    
    name: str = "base"
    app_name: str = "unknown"
    
    def __init__(self):
        self.attached = False
        self.window_handle = None
        self.chat_region: Optional[Tuple[int, int, int, int]] = None
        self.input_region: Optional[Tuple[int, int, int, int]] = None
    
    @abstractmethod
    def attach(self) -> bool:
        """
        附加到运行中的 IM 应用
        
        Returns:
            是否成功
        """
        pass
    
    @abstractmethod
    def open_chat(self, contact: str) -> bool:
        """
        打开指定聊天
        
        Args:
            contact: 联系人名称
        
        Returns:
            是否成功
        """
        pass
    
    @abstractmethod
    def type_message(self, text: str):
        """
        输入消息
        
        Args:
            text: 消息内容
        """
        pass
    
    @abstractmethod
    def send(self):
        """发送消息"""
        pass
    
    def get_chat_list(self) -> List[ChatInfo]:
        """
        获取聊天列表
        
        Returns:
            聊天信息列表
        """
        return []
    
    def click(self, x: int, y: int, button: str = "left"):
        """
        点击指定位置
        
        Args:
            x: X 坐标
            y: Y 坐标
            button: 鼠标按钮 (left/right/middle)
        """
        import pyautogui
        
        pyautogui.click(x, y, button=button)
        logger.debug(f"Clicked at ({x}, {y})")
    
    def double_click(self, x: int, y: int):
        """双击"""
        import pyautogui
        pyautogui.doubleClick(x, y)
        logger.debug(f"Double clicked at ({x}, {y})")
    
    def scroll(self, clicks: int, x: Optional[int] = None, y: Optional[int] = None):
        """
        滚动
        
        Args:
            clicks: 滚动量（正数向上，负数向下）
            x, y: 滚动位置（可选）
        """
        import pyautogui
        pyautogui.scroll(clicks, x, y)
        logger.debug(f"Scrolled {clicks} at ({x}, {y})")
    
    def press_key(self, key: str, presses: int = 1, interval: float = 0.1):
        """
        按键
        
        Args:
            key: 键名 (enter/ctrl+c 等)
            presses: 按压次数
            interval: 间隔
        """
        import pyautogui
        pyautogui.press(key, presses=presses, interval=interval)
        logger.debug(f"Pressed key: {key}")
    
    def hotkey(self, *keys):
        """
        快捷键
        
        Args:
            keys: 键列表 (如 "ctrl", "v")
        """
        import pyautogui
        pyautogui.hotkey(*keys)
        logger.debug(f"Pressed hotkey: {keys}")
    
    def find_window(self, title_pattern: str) -> Optional[int]:
        """
        查找窗口
        
        Args:
            title_pattern: 窗口标题模式
        
        Returns:
            窗口句柄或 None
        """
        try:
            import pygetwindow as gw
            
            for window in gw.getAllWindows():
                if title_pattern.lower() in window.title.lower():
                    self.window_handle = window
                    return window
        except ImportError:
            logger.debug("pygetwindow not installed")
        
        return None
    
    def bring_to_front(self):
        """将窗口带到前台"""
        if self.window_handle:
            try:
                self.window_handle.activate()
            except:
                pass
