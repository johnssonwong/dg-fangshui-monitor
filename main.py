import asyncio
from playwright.async_api import async_playwright
import requests
from datetime import datetime, timedelta

# ====== Telegram 配置 ======
BOT_TOKEN = "8134230045:AAForY5xzO6D4EioSYNfk1yPtF6-cl50ABI"
CHAT_ID = "485427847"

last_status = None
fangshui_start_time = None

# ====== 发送 Telegram 消息 ======
def send_telegram_message(message: str):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": message}
    try:
        requests.post(url, data=payload)
        print(f"已发送 Telegram 消息：{message}")
    except Exception as e:
        print("Telegram 发送失败：", e)

# ====== 根据牌桌走势分类 ======
def classify_tables(table_patterns):
    total = len(table_patterns)
    fangshui_like = sum(1 for t in table_patterns if "连" in t or "长龙" in t)
    ratio = (fangshui_like / total) * 100 if total > 0 else 0

    if ratio >= 70:
        return "放水时段（提高胜率）"
    elif 55 <= ratio < 70:
        return "中等胜率（中上）"
    elif 30 <= ratio < 55:
        return "胜率中等"
    else:
        return "收割时段"

# ====== 获取 DG 平台牌桌数据 ======
async def fetch_dg_tables(page):
    tables = []
    elements = await page.query_selector_all(".table-road")
    for el in elements:
        text = await el.inner_text()
        tables.append(text.strip())
    return tables

# ====== 自动选择 Free / 免费试玩 进入平台 ======
async def enter_platform(page):
    try:
        await page.click("text=Free")
        await asyncio.sleep(5)
        return True
    except:
        try:
            await page.click("text=免费试玩")
            await asyncio.sleep(5)
            return True
        except:
            return False

# ====== 主检测逻辑 ======
async def monitor_dg():
    global last_status, fangshui_start_time
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        # 打开入口网址
        try:
            await page.goto("https://dg18.co/")
        except:
            await page.goto("https://dg18.co/wap/")
        await asyncio.sleep(3)

        entered = await enter_platform(page)
        if not entered:
            print("未能进入 DG 平台")
            await browser.close()
            return

        # 获取牌桌走势
        table_patterns = await fetch_dg_tables(page)
        current_status = classify_tables(table_patterns)

        now = datetime.utcnow() + timedelta(hours=8)  # 马来西亚时区
        print(f"{now} 当前状态：{current_status}")

        # ====== 判断提醒 ======
        if current_status == "放水时段（提高胜率）":
            if last_status != "放水时段（提高胜率）":
                fangshui_start_time = now
                send_telegram_message("🔥 放水时段（提高胜率）开始！")
        elif current_status == "中等胜率（中上）":
            if last_status != "中等胜率（中上）":
                send_telegram_message("⚠ 类似放水时段【中等胜率(中上)】。")
        else:
            if last_status == "放水时段（提高胜率）" and fangshui_start_time:
                duration = (now - fangshui_start_time).seconds // 60
                send_telegram_message(f"❌ 放水已结束，共持续 {duration} 分钟。")
                fangshui_start_time = None

        last_status = current_status
        await browser.close()

if __name__ == "__main__":
    asyncio.run(monitor_dg())
