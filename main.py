import time
import requests
import datetime

# ======== 配置部分（已填好你的资料） ========
BOT_TOKEN = "8134230045:AAForY5xzO6D4EioSYNfk1yPtF6-cl50ABI"
CHAT_ID = "485427847"

# 假设的检测函数（需后续替换成真实DG检测逻辑）
def check_dg_tables():
    """
    模拟检测 DG 平台。
    实际逻辑需用 Selenium + OpenCV 识别放水/收割/中等结构。
    返回值：
        "fangshui"  -> 放水时段
        "medium_up" -> 中等胜率（中上）
        "medium"    -> 胜率中等
        "shouge"    -> 收割时段
    """
    # 这里先模拟，后面接入真实识别
    # TODO: 替换成DG平台的实时图像识别
    return "fangshui"

# 发送 Telegram 消息
def send_telegram(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text}
    try:
        requests.post(url, data=payload)
    except Exception as e:
        print(f"Telegram发送失败: {e}")

# ======== 主检测逻辑 ========
def main():
    print("启动 DG Fangshui 自动检测脚本...")
    last_status = None
    fangshui_start = None

    while True:
        status = check_dg_tables()
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if status == "fangshui":
            if last_status != "fangshui":
                fangshui_start = time.time()
                send_telegram(f"🟢 [{now}] 检测到【放水时段（提高胜率）】！立即留意入场机会。")
            else:
                # 每次循环仅提醒一次，不刷屏
                pass

        elif status == "medium_up":
            if last_status != "medium_up":
                send_telegram(f"🟡 [{now}] 检测到【类似放水时段【中等胜率(中上)】】，请注意观察。")

        elif status in ["medium", "shouge"]:
            if last_status == "fangshui" and fangshui_start:
                duration = int((time.time() - fangshui_start) / 60)
                send_telegram(f"❌ [{now}] 放水已结束，共持续 {duration} 分钟。")
                fangshui_start = None

        last_status = status
        time.sleep(300)  # 每5分钟检测一次

if __name__ == "__main__":
    main()
