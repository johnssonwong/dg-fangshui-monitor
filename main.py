import asyncio
from playwright.async_api import async_playwright
import requests
import time
from datetime import datetime, timedelta

# ====== 你的 Telegram 配置 ======
BOT_TOKEN = "8134230045:AAForY5xzO6D4EioSYNfk1yPtF6-cl50ABI"
CHAT_ID = "485427847"

# ====== 全局状态 ======
last_status = None
fangshui_start_time = None

# ====== 发送 Telegram 消息 ======
def send_telegram_message(message: str):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message}
    try:
        requests.post(url, data=payload)
    except Exception as e:
        print("Telegram 发送失败：", e)

# ====== 判断牌桌状态逻辑 ======
def classify_tables(table_patterns):
    """
    根据传入的牌桌结构（简单用文字模拟）判断当前时段。
    table_patterns: List[str] 每张桌子的牌路，如 "长龙", "单跳", "乱局"
    """
    total = len(table_patterns)
    fangshui_like = sum(1 for t in table_patterns if t == "长龙" or t == "多连")

    ratio = (fangshui_like / total) * 100 if total > 0 else 0

    if ratio >= 70:
        return "放水时段（提高胜率）"
    elif 55 <= ratio < 70:
        return "中等胜率（中上）"
    elif 30 <= ratio < 55:
        return "胜率中等"
    else:
        return "收割时段"

# ====== 主流程 ======
async def monitor_dg():
    global last_status, fangshui_start_time

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto("https://dg18.co/wap/")

        # 自动点击“免费试玩”
        try:
            await page.click("text=免费试玩")
            await asyncio.sleep(5)
        except:
            print("未找到 '免费试玩' 按钮")

        # 模拟抓取牌桌数据（实际中可用 page.query_selector_all）
        # 这里暂时用假数据模拟，后期可用 DOM 抓取
        table_patterns = ["长龙", "长龙", "乱局", "多连", "乱局", "长龙"]  # 模拟

        current_status = classify_tables(table_patterns)
        print(f"{datetime.now()} 当前状态：{current_status}")

        if current_status == "放水时段（提高胜率）":
            if last_status != "放水时段（提高胜率）":
                fangshui_start_time = datetime.now()
                send_telegram_message("🔥 放水时段（提高胜率）开始！请留意入场！")
        elif current_status == "中等胜率（中上）":
            if last_status != "中等胜率（中上）":
                send_telegram_message("⚠ 接近放水时段（中等胜率中上）。")
        else:
            if last_status == "放水时段（提高胜率）" and fangshui_start_time:
                duration = (datetime.now() - fangshui_start_time).seconds // 60
                send_telegram_message(f"❌ 放水已结束，共持续 {duration} 分钟。")
                fangshui_start_time = None

        last_status = current_status
        await browser.close()

if __name__ == "__main__":
    asyncio.run(monitor_dg())
