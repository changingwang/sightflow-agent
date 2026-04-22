"""
屏幕扫描器 - 截图和 UI 元素检测
"""

import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path

logger = logging.getLogger(__name__)


@dataclass
class UIElement:
    """UI 元素"""
    element_type: str  # "unread_dot", "chat_item", "message_bubble", "input_field"
    position: Tuple[int, int, int, int]  # (x, y, width, height)
    confidence: float
    metadata: Optional[Dict] = None


class ScreenScanner:
    """
    屏幕扫描器
    
    负责截图和识别 UI 元素。
    """
    
    def __init__(self, scale: float = 1.0):
        """
        初始化扫描器
        
        Args:
            scale: 截图缩放比例（1.0 = 原始分辨率）
        """
        self.scale = scale
        self._templates = {}
    
    def capture(self, region: Optional[Tuple[int, int, int, int]] = None) -> "Image":
        """
        截取屏幕
        
        Args:
            region: 截取区域 (x, y, width, height)，None 表示全屏
        
        Returns:
            PIL Image 对象
        """
        try:
            import pyautogui
            
            if region:
                screenshot = pyautogui.screenshot(region=region)
            else:
                screenshot = pyautogui.screenshot()
            
            logger.debug(f"Captured screenshot: {screenshot.size}")
            return screenshot
            
        except ImportError:
            logger.error("pyautogui not installed. Run: pip install pyautogui")
            raise
    
    def detect_unread_dots(
        self,
        image: "Image",
        app: str = "wechat",
    ) -> List[Dict]:
        """
        检测未读消息红点
        
        Args:
            image: 截图
            app: 应用名称 (wechat/whatsapp)
        
        Returns:
            红点位置列表，每个包含 {"position": (x, y), "count": N}
        """
        # 加载红点模板
        template = self._load_unread_template(app)
        
        if template is None:
            # 使用颜色检测 fallback
            return self._detect_red_dots_by_color(image)
        
        # 模板匹配
        dots = self._template_match(image, template)
        
        logger.info(f"Detected {len(dots)} unread dots for {app}")
        return dots
    
    def detect_chat_list(self, image: "Image", app: str = "wechat") -> List[Dict]:
        """
        检测聊天列表
        
        Returns:
            聊天项列表，每个包含 {"name": str, "position": (x, y, w, h), "last_message": str}
        """
        # 基于布局分析检测聊天项
        items = []
        
        # 微信聊天列表通常在左侧，固定宽度
        if app == "wechat":
            chat_list_region = (0, 100, 250, image.height - 100)
            items = self._detect_wechat_chat_list(image, chat_list_region)
        
        elif app == "whatsapp":
            chat_list_region = (0, 60, 350, image.height - 60)
            items = self._detect_whatsapp_chat_list(image, chat_list_region)
        
        return items
    
    def detect_input_field(self, image: "Image", app: str = "wechat") -> Optional[Dict]:
        """
        检测输入框位置
        
        Returns:
            输入框位置 {"position": (x, y, w, h)} 或 None
        """
        # 输入框通常在窗口底部
        bottom_region = (0, image.height - 150, image.width, 150)
        
        # 检测输入框特征（圆角矩形、灰色边框）
        input_field = self._detect_input_by_shape(image, bottom_region)
        
        return input_field
    
    def find_element(
        self,
        image: "Image",
        element_type: str,
        app: str = "wechat",
    ) -> Optional[UIElement]:
        """
        查找指定类型的 UI 元素
        
        Args:
            image: 截图
            element_type: 元素类型
            app: 应用名称
        
        Returns:
            UIElement 或 None
        """
        if element_type == "unread_dot":
            dots = self.detect_unread_dots(image, app)
            if dots:
                dot = dots[0]
                return UIElement(
                    element_type="unread_dot",
                    position=(*dot["position"], 20, 20),
                    confidence=0.9,
                )
        
        elif element_type == "input_field":
            field = self.detect_input_field(image, app)
            if field:
                return UIElement(
                    element_type="input_field",
                    position=field["position"],
                    confidence=0.85,
                )
        
        return None
    
    def register_template(self, name: str, path: str):
        """
        注册 UI 模板图片
        
        Args:
            name: 模板名称
            path: 图片路径
        """
        from PIL import Image
        self._templates[name] = Image.open(path)
        logger.debug(f"Registered template: {name}")
    
    # ========== 内部方法 ==========
    
    def _load_unread_template(self, app: str) -> Optional["Image"]:
        """加载未读红点模板"""
        template_name = f"{app}_unread_dot"
        return self._templates.get(template_name)
    
    def _detect_red_dots_by_color(self, image: "Image") -> List[Dict]:
        """通过颜色检测红点（fallback 方案）"""
        import numpy as np
        
        img_array = np.array(image)
        
        # 红色检测（RGB 阈值）
        red_mask = (
            (img_array[:, :, 0] > 200) &  # R 高
            (img_array[:, :, 1] < 100) &  # G 低
            (img_array[:, :, 2] < 100)    # B 低
        )
        
        # 查找连通区域
        from scipy import ndimage
        labeled, num_features = ndimage.label(red_mask)
        
        dots = []
        for i in range(1, num_features + 1):
            positions = np.where(labeled == i)
            if len(positions[0]) > 10:  # 最小面积过滤
                y_center = int(np.mean(positions[0]))
                x_center = int(np.mean(positions[1]))
                dots.append({
                    "position": (x_center, y_center),
                    "count": 1,  # 无法从颜色判断数量
                })
        
        return dots
    
    def _template_match(self, image: "Image", template: "Image") -> List[Dict]:
        """模板匹配"""
        import cv2
        import numpy as np
        
        img_array = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)
        tpl_array = cv2.cvtColor(np.array(template), cv2.COLOR_RGB2BGR)
        
        # 模板匹配
        result = cv2.matchTemplate(img_array, tpl_array, cv2.TM_CCOEFF_NORMED)
        
        # 查找匹配点
        threshold = 0.8
        locations = np.where(result >= threshold)
        
        dots = []
        for pt in zip(*locations[::-1]):
            dots.append({
                "position": (pt[0] + template.width // 2, pt[1] + template.height // 2),
                "count": 1,
            })
        
        # 非极大值抑制（去重）
        dots = self._non_max_suppression(dots, threshold=20)
        
        return dots
    
    def _detect_wechat_chat_list(self, image: "Image", region: Tuple) -> List[Dict]:
        """检测微信聊天列表"""
        # 简化实现：返回固定布局
        return [
            {"name": "Chat 1", "position": (10, 110, 230, 60), "last_message": ""},
        ]
    
    def _detect_whatsapp_chat_list(self, image: "Image", region: Tuple) -> List[Dict]:
        """检测 WhatsApp 聊天列表"""
        return [
            {"name": "Chat 1", "position": (10, 70, 330, 70), "last_message": ""},
        ]
    
    def _detect_input_by_shape(self, image: "Image", region: Tuple) -> Optional[Dict]:
        """通过形状检测输入框"""
        # 简化实现：返回区域底部
        x, y, w, h = region
        return {
            "position": (x + 10, y + h - 50, w - 20, 40),
        }
    
    def _non_max_suppression(self, dots: List[Dict], threshold: int) -> List[Dict]:
        """非极大值抑制去重"""
        if not dots:
            return []
        
        filtered = []
        for dot in dots:
            is_duplicate = False
            for existing in filtered:
                dx = abs(dot["position"][0] - existing["position"][0])
                dy = abs(dot["position"][1] - existing["position"][1])
                if dx < threshold and dy < threshold:
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                filtered.append(dot)
        
        return filtered


# 延迟导入 PIL
try:
    from PIL import Image
except ImportError:
    Image = None
