import os
import time
import requests
from datetime import datetime, timedelta
import pytz

# ====== Telegram 配置 ======
BOT_TOKEN = "8134230045:AAForY5xzO6D4EioSYNfk1yPtF6-cl50ABI"
CHAT_ID = "485427847"

# ====== 时区设置（马来西亚） ======
tz = pytz.timezone('Asia/Kuala_Lumpur')

# ====== 自动创建模板目录 ======
TEMPLATE_DIR = "templates"
os.makedirs(f"{TEMPLATE_DIR}/fangshui", exist_ok=True)
os.makedirs(f"{TEMPLATE_DIR}/medium", exist_ok=True)
os.makedirs(f"{TEMPLATE_DIR}/shouge", exist_ok=True)

# ====== Telegram 发送消息 ======
def send_telegram(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": message}
    try:
        requests.post(url, data=data)
    except Exception as e:
        print(f"Telegram发送失败: {e}")

# ====== DG 平台检测逻辑 ======
def analyze_dg_platform():
    """
    实时分析 DG 平台桌面走势：
    1. 检测是否有大量长龙、多连。
    2. 检测是否单跳频繁。
    3. 使用已上传的 fangshui/shouge/medium 样本图片做图像匹配。
    返回：
    - "fangshui"      放水时段
    - "medium_high"   类似放水（中等胜率中上）
    - "medium"        胜率中等
    - "shouge"        收割时段
    """
    # TODO: 在这里实现真实网页检测 + 图像比对逻辑
    # 当前仅作占位符
    return "fangshui"  # 测试时固定返回放水

# ====== 主循环 ======
def main():
    last_status = None
    fangshui_start_time = None
    fangshui_end_estimate = None

    print("启动 DG 平台自动检测 (24h, 马来西亚时区 GMT+8)...")
    while True:
        current_time = datetime.now(tz)
        status = analyze_dg_platform()

        if status == "fangshui":
            if last_status != "fangshui":
                fangshui_start_time = current_time
                fangshui_end_estimate = current_time + timedelta(minutes=30)  # 默认预计放水30分钟
                send_telegram(
                    f"🔥 {current_time.strftime('%Y-%m-%d %H:%M:%S')}\n"
                    f"检测到【放水时段（提高胜率）】！\n"
                    f"预计结束时间：{fangshui_end_estimate.strftime('%H:%M')}。"
                )
            last_status = "fangshui"

        elif status == "medium_high":
            if last_status != "medium_high":
                send_telegram(
                    f"⚠ {current_time.strftime('%Y-%m-%d %H:%M:%S')}\n"
                    f"检测到【类似放水时段（中等胜率中上）】。\n请留意台桌走势。"
                )
            last_status = "medium_high"

        else:
            if last_status == "fangshui" and fangshui_start_time:
                duration = int((current_time - fangshui_start_time).total_seconds() / 60)
                send_telegram(
                    f"🔴 {current_time.strftime('%Y-%m-%d %H:%M:%S')}\n"
                    f"放水已结束，共持续 {duration} 分钟。"
                )
                fangshui_start_time = None
            last_status = status

        time.sleep(60)  # 每分钟检测一次

if __name__ == "__main__":
    main()
