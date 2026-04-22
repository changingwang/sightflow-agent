"""
SightFlow 使用示例
"""

# ========== 示例 1: 基础微信操作 ==========

def example_wechat_basic():
    """微信基础操作示例"""
    from sightflow_agent import VisionAgent, WeChatDriver
    
    # 创建驱动和 Agent
    driver = WeChatDriver()
    agent = VisionAgent(driver=driver)
    
    # 附加到微信
    if not driver.attach():
        print("无法连接到微信")
        return
    
    # 发送消息
    agent.send_message("豆哥", "你好！我是 SightFlow Agent 👋")
    
    # 读取消息
    messages = agent.read_chat("豆哥", limit=5)
    for msg in messages:
        print(f"{msg.sender}: {msg.text}")
    
    # 检查未读
    unread = agent.detect_unread()
    print(f"未读消息：{len(unread)} 条")


# ========== 示例 2: 自动回复 ==========

def example_auto_reply():
    """自动回复示例"""
    from sightflow_agent import VisionAgent, WeChatDriver
    
    driver = WeChatDriver()
    agent = VisionAgent(driver=driver)
    
    if not driver.attach():
        return
    
    # 智能模式自动回复
    print("启动自动回复...")
    
    try:
        agent.auto_reply(mode="smart", interval=10)
    except KeyboardInterrupt:
        agent.stop()
        print("自动回复已停止")


# ========== 示例 3: 关键词回复 ==========

def example_keyword_reply():
    """关键词回复示例"""
    from sightflow_agent import VisionAgent, WeChatDriver
    
    driver = WeChatDriver()
    agent = VisionAgent(driver=driver)
    
    if not driver.attach():
        return
    
    # 定义关键词回复
    keywords = {
        "你好": "你好！有什么可以帮你的吗？",
        "在吗": "在的，请说～",
        "谢谢": "不客气！😊",
        "再见": "拜拜，下次聊！",
    }
    
    print("启动关键词自动回复...")
    
    try:
        agent.auto_reply(mode="keyword", keywords=keywords, interval=5)
    except KeyboardInterrupt:
        agent.stop()


# ========== 示例 4: OpenClaw 集成 ==========

def example_openclaw():
    """OpenClaw 技能示例"""
    from sightflow_agent.skills import OpenClawWeChat
    
    skill = OpenClawWeChat()
    
    # 发送消息
    result = skill.send_message("豆哥", "任务已完成！")
    print(f"发送结果：{result}")
    
    # 读取消息
    result = skill.read_messages("豆哥", limit=5)
    print(f"消息列表：{result}")
    
    # 检查未读
    result = skill.check_unread()
    print(f"未读消息：{result}")


# ========== 示例 5: Hermes Agent 集成 ==========

def example_hermes():
    """Hermes Agent 工具示例"""
    from sightflow_agent.tools import wechat_tool
    
    # 发送消息
    result = wechat_tool._run(
        action="send_message",
        contact="豆哥",
        message="Hello from Hermes!"
    )
    print(f"发送结果：{result}")
    
    # 读取消息
    result = wechat_tool._run(
        action="read_messages",
        contact="豆哥",
        limit=5
    )
    print(f"消息列表：{result}")


# ========== 示例 6: 屏幕截图 ==========

def example_screenshot():
    """截图示例"""
    from sightflow_agent import ScreenScanner
    
    scanner = ScreenScanner()
    
    # 全屏截图
    screenshot = scanner.capture()
    screenshot.save("full_screen.png")
    
    # 区域截图
    region_screenshot = scanner.capture(region=(0, 0, 500, 500))
    region_screenshot.save("region.png")
    
    print("截图已保存")


# ========== 示例 7: OCR 文字识别 ==========

def example_ocr():
    """OCR 示例"""
    from sightflow_agent import ScreenScanner, OCR
    from sightflow_agent.drivers import WeChatDriver
    
    driver = WeChatDriver()
    driver.attach()
    
    scanner = ScreenScanner()
    ocr = OCR()
    
    # 截图
    screenshot = scanner.capture(region=driver.chat_region)
    
    # 识别文字
    text = ocr.recognize(screenshot)
    print(f"识别结果：{text}")
    
    # 提取文字区域
    regions = ocr.extract_text_regions(screenshot)
    print(f"文字区域数量：{len(regions)}")


# ========== 运行示例 ==========

if __name__ == "__main__":
    import sys
    
    examples = {
        "wechat": example_wechat_basic,
        "auto_reply": example_auto_reply,
        "keyword": example_keyword_reply,
        "openclaw": example_openclaw,
        "hermes": example_hermes,
        "screenshot": example_screenshot,
        "ocr": example_ocr,
    }
    
    if len(sys.argv) < 2:
        print("用法：python examples.py <example_name>")
        print(f"可用示例：{', '.join(examples.keys())}")
        sys.exit(1)
    
    example_name = sys.argv[1]
    
    if example_name in examples:
        print(f"运行示例：{example_name}")
        examples[example_name]()
    else:
        print(f"未知示例：{example_name}")
        sys.exit(1)
