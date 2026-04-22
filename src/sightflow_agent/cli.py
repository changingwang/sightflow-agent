"""
SightFlow CLI - 命令行工具
"""

import argparse
import sys
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def cmd_init(args):
    """初始化配置"""
    from pathlib import Path
    
    config_dir = Path.home() / ".sightflow"
    config_dir.mkdir(exist_ok=True)
    
    config_file = config_dir / "config.json"
    if not config_file.exists():
        config_file.write_text(json.dumps({
            "app": "wechat",
            "ocr_engine": "auto",
            "debug": False,
        }, indent=2))
    
    print(f"✅ Config initialized: {config_file}")
    return 0


def cmd_unread(args):
    """检测未读消息"""
    from .agent import VisionAgent
    from .drivers import WeChatDriver, WhatsAppDriver
    
    app = args.app or "wechat"
    
    if app == "wechat":
        driver = WeChatDriver()
    elif app == "whatsapp":
        driver = WhatsAppDriver()
    else:
        print(f"❌ Unknown app: {app}")
        return 1
    
    agent = VisionAgent(driver=driver)
    
    if not driver.attach():
        print(f"❌ Failed to attach to {app}")
        return 1
    
    unread = agent.detect_unread()
    
    if not unread:
        print("✅ No unread messages")
    else:
        print(f"📬 Found {len(unread)} unread:")
        for n in unread:
            print(f"   • {n.contact}: {n.count} messages")
    
    if args.count:
        print(f"\nTotal: {sum(n.count for n in unread)} messages")
    
    return 0


def cmd_read(args):
    """读取聊天"""
    from .agent import VisionAgent
    from .drivers import WeChatDriver, WhatsAppDriver
    
    app = args.app or "wechat"
    contact = args.contact
    
    if not contact:
        print("❌ Contact required")
        return 1
    
    if app == "wechat":
        driver = WeChatDriver()
    elif app == "whatsapp":
        driver = WhatsAppDriver()
    else:
        print(f"❌ Unknown app: {app}")
        return 1
    
    agent = VisionAgent(driver=driver)
    
    if not driver.attach():
        print(f"❌ Failed to attach to {app}")
        return 1
    
    messages = agent.read_chat(contact, limit=args.limit)
    
    if not messages:
        print("📭 No messages found")
    else:
        print(f"📖 Messages from {contact}:")
        for msg in messages:
            print(f"   {msg.sender}: {msg.text}")
    
    return 0


def cmd_send(args):
    """发送消息"""
    from .agent import VisionAgent
    from .drivers import WeChatDriver, WhatsAppDriver
    
    app = args.app or "wechat"
    contact = args.contact
    message = args.message
    
    if not contact or not message:
        print("❌ Contact and message required")
        return 1
    
    if app == "wechat":
        driver = WeChatDriver()
    elif app == "whatsapp":
        driver = WhatsAppDriver()
    else:
        print(f"❌ Unknown app: {app}")
        return 1
    
    agent = VisionAgent(driver=driver)
    
    if not driver.attach():
        print(f"❌ Failed to attach to {app}")
        return 1
    
    agent.send_message(contact, message)
    print(f"✅ Message sent to {contact}")
    
    return 0


def cmd_auto_reply(args):
    """自动回复"""
    from .agent import VisionAgent
    from .drivers import WeChatDriver, WhatsAppDriver
    
    app = args.app or "wechat"
    mode = args.mode or "smart"
    
    if app == "wechat":
        driver = WeChatDriver()
    elif app == "whatsapp":
        driver = WhatsAppDriver()
    else:
        print(f"❌ Unknown app: {app}")
        return 1
    
    agent = VisionAgent(driver=driver)
    
    if not driver.attach():
        print(f"❌ Failed to attach to {app}")
        return 1
    
    print(f"🤖 Starting auto-reply ({mode} mode)...")
    print("Press Ctrl+C to stop")
    
    try:
        agent.auto_reply(mode=mode, interval=args.interval)
    except KeyboardInterrupt:
        agent.stop()
        print("\n👋 Auto-reply stopped")
    
    return 0


def cmd_run(args):
    """运行工作流"""
    from pathlib import Path
    
    workflow_file = Path(args.workflow)
    
    if not workflow_file.exists():
        print(f"❌ Workflow not found: {workflow_file}")
        return 1
    
    # TODO: 实现工作流引擎
    print(f"📋 Running workflow: {workflow_file}")
    print("Workflow engine not yet implemented")
    
    return 0


def cmd_screenshot(args):
    """截图测试"""
    from .scanner import ScreenScanner
    from pathlib import Path
    
    scanner = ScreenScanner()
    
    region = None
    if args.region:
        region = tuple(map(int, args.region.split(",")))
    
    screenshot = scanner.capture(region)
    
    output = args.output or "screenshot.png"
    screenshot.save(output)
    
    print(f"✅ Screenshot saved: {output}")
    return 0


def cmd_calibrate(args):
    """校准"""
    from .drivers import WeChatDriver, WhatsAppDriver
    
    app = args.app or "wechat"
    
    if app == "wechat":
        driver = WeChatDriver()
    elif app == "whatsapp":
        driver = WhatsAppDriver()
    else:
        print(f"❌ Unknown app: {app}")
        return 1
    
    if not driver.attach():
        print(f"❌ Failed to attach to {app}")
        return 1
    
    print(f"🔧 Calibrating {app}...")
    driver.calibrate()
    
    return 0


def main():
    """CLI 入口"""
    parser = argparse.ArgumentParser(
        prog="sightflow",
        description="👁️ SightFlow - 视觉驱动的通用 IM Agent",
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # init
    init_parser = subparsers.add_parser("init", help="初始化配置")
    init_parser.set_defaults(func=cmd_init)
    
    # unread
    unread_parser = subparsers.add_parser("unread", help="检测未读消息")
    unread_parser.add_argument("--app", choices=["wechat", "whatsapp"])
    unread_parser.add_argument("--count", action="store_true", help="显示总数")
    unread_parser.set_defaults(func=cmd_unread)
    
    # read
    read_parser = subparsers.add_parser("read", help="读取聊天")
    read_parser.add_argument("--app", choices=["wechat", "whatsapp"])
    read_parser.add_argument("--contact", required=True)
    read_parser.add_argument("--limit", type=int, default=10)
    read_parser.set_defaults(func=cmd_read)
    
    # send
    send_parser = subparsers.add_parser("send", help="发送消息")
    send_parser.add_argument("--app", choices=["wechat", "whatsapp"])
    send_parser.add_argument("--contact", required=True)
    send_parser.add_argument("--message", required=True)
    send_parser.set_defaults(func=cmd_send)
    
    # auto-reply
    reply_parser = subparsers.add_parser("auto-reply", help="自动回复")
    reply_parser.add_argument("--app", choices=["wechat", "whatsapp"])
    reply_parser.add_argument("--mode", choices=["smart", "keyword", "ai"])
    reply_parser.add_argument("--interval", type=int, default=5)
    reply_parser.set_defaults(func=cmd_auto_reply)
    
    # run
    run_parser = subparsers.add_parser("run", help="运行工作流")
    run_parser.add_argument("--workflow", required=True)
    run_parser.set_defaults(func=cmd_run)
    
    # screenshot
    shot_parser = subparsers.add_parser("screenshot", help="截图测试")
    shot_parser.add_argument("--region", help="区域 (x,y,w,h)")
    shot_parser.add_argument("--output", "-o")
    shot_parser.set_defaults(func=cmd_screenshot)
    
    # calibrate
    cal_parser = subparsers.add_parser("calibrate", help="校准 UI")
    cal_parser.add_argument("--app", choices=["wechat", "whatsapp"])
    cal_parser.set_defaults(func=cmd_calibrate)
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 0
    
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
