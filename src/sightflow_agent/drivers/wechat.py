"""
微信驱动器 - 操作微信 Windows/macOS 客户端
"""

import logging
import time
from typing import List, Optional, Tuple

from .base import BaseDriver, ChatInfo

logger = logging.getLogger(__name__)


class WeChatDriver(BaseDriver):
    """
    微信驱动器
    
    通过视觉识别和模拟输入操作微信。
    """
    
    name = "wechat"
    app_name = "wechat"
    
    # 微信窗口特征
    WINDOW_TITLE = "微信"
    
    # UI 区域（默认值，可校准）
    DEFAULT_CHAT_LIST_REGION = (0, 100, 250, 600)  # 左侧聊天列表
    DEFAULT_CHAT_REGION = (250, 100, 500, 500)     # 中间聊天区域
    DEFAULT_INPUT_REGION = (250, 600, 500, 80)     # 底部输入框
    
    def __init__(self):
        super().__init__()
        self.chat_list_region = self.DEFAULT_CHAT_LIST_REGION
        self.chat_region = self.DEFAULT_CHAT_REGION
        self.input_region = self.DEFAULT_INPUT_REGION
    
    def attach(self) -> bool:
        """附加到微信"""
        logger.info("Attaching to WeChat...")
        
        # 查找微信窗口
        window = self.find_window(self.WINDOW_TITLE)
        
        if window:
            self.window_handle = window
            self.bring_to_front()
            time.sleep(0.5)  # 等待窗口激活
            
            self.attached = True
            logger.info("Attached to WeChat successfully")
            return True
        
        logger.warning("WeChat window not found. Make sure WeChat is running.")
        return False
    
    def open_chat(self, contact: str) -> bool:
        """打开聊天"""
        if not self.attached:
            if not self.attach():
                return False
        
        logger.info(f"Opening chat with: {contact}")
        
        # 方法 1: 使用搜索框
        if self._search_and_open(contact):
            return True
        
        # 方法 2: 在聊天列表中查找
        if self._find_in_chat_list(contact):
            return True
        
        logger.warning(f"Could not open chat: {contact}")
        return False
    
    def type_message(self, text: str):
        """输入消息"""
        if not self.input_region:
            logger.error("Input region not set")
            return
        
        # 点击输入框
        x = self.input_region[0] + 50
        y = self.input_region[1] + 20
        self.click(x, y)
        
        time.sleep(0.2)
        
        # 输入文字
        import pyautogui
        pyautogui.write(text, interval=0.05)
        logger.debug(f"Typed message: {text[:30]}...")
    
    def send(self):
        """发送消息（按 Enter）"""
        self.press_key("enter")
        logger.debug("Message sent")
    
    def get_chat_list(self) -> List[ChatInfo]:
        """获取聊天列表"""
        # TODO: 实现视觉识别聊天列表
        return []
    
    def click_unread(self, index: int = 0) -> bool:
        """
        点击未读消息
        
        Args:
            index: 第几个未读消息
        """
        # TODO: 实现未读消息点击
        return False
    
    def get_unread_count(self) -> int:
        """获取未读消息总数"""
        # TODO: 实现未读计数识别
        return 0
    
    # ========== 内部方法 ==========
    
    def _search_and_open(self, contact: str) -> bool:
        """通过搜索打开聊天"""
        try:
            import pyautogui
            
            # Ctrl+F 打开搜索
            self.hotkey("ctrl", "f")
            time.sleep(0.3)
            
            # 输入联系人名称
            pyautogui.write(contact, interval=0.1)
            time.sleep(0.5)
            
            # 按 Enter 选择第一个结果
            self.press_key("enter")
            time.sleep(0.3)
            
            logger.debug(f"Searched and opened: {contact}")
            return True
            
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return False
    
    def _find_in_chat_list(self, contact: str) -> bool:
        """在聊天列表中查找并点击"""
        # TODO: 实现视觉识别聊天列表项
        return False
    
    def calibrate(self):
        """
        校准 UI 区域
        
        运行此方法后，按提示点击各个区域以校准坐标。
        """
        print("=== 微信 UI 校准 ===")
        print("请点击聊天列表区域...")
        self._calibrate_region("chat_list")
        
        print("请点击聊天内容区域...")
        self._calibrate_region("chat")
        
        print("请点击输入框区域...")
        self._calibrate_region("input")
        
        print("校准完成！")
    
    def _calibrate_region(self, name: str):
        """校准单个区域"""
        import pyautogui
        
        # 等待用户点击
        print("5 秒后开始记录坐标，请点击目标区域...")
        time.sleep(5)
        
        pos = pyautogui.position()
        print(f"记录坐标：{pos}")
        
        # 根据区域类型设置
        if name == "chat_list":
            self.chat_list_region = (pos[0] - 100, pos[1] - 50, 250, 400)
        elif name == "chat":
            self.chat_region = (pos[0] - 200, pos[1] - 100, 500, 400)
        elif name == "input":
            self.input_region = (pos[0] - 200, pos[1] - 20, 500, 60)
