import os
import time
import requests
from datetime import datetime
import pytz
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from PIL import Image
import cv2
import numpy as np

# ===== Telegram 配置 =====
BOT_TOKEN = "8134230045:AAForY5xzO6D4EioSYNfk1yPtF6-cl50ABI"
CHAT_ID = "485427847"

# ===== 时区设置（马来西亚） =====
tz = pytz.timezone('Asia/Kuala_Lumpur')

# ===== 样本模板路径 =====
TEMPLATES_PATH = "templates"

# ===== 状态缓存 =====
STATUS_FILE = "status_cache.txt"

def send_telegram(message):
    """发送Telegram消息"""
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": message}
    try:
        requests.post(url, data=data)
    except Exception as e:
        print(f"Telegram发送失败: {e}")

def save_status(status, start_time=None):
    with open(STATUS_FILE, "w") as f:
        f.write(f"{status}|{start_time if start_time else ''}")

def load_status():
    if os.path.exists(STATUS_FILE):
        with open(STATUS_FILE, "r") as f:
            parts = f.read().split("|")
            return parts[0], parts[1] if len(parts) > 1 else ''
    return None, None

def open_dg_and_screenshot():
    """使用Selenium访问DG并截图"""
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")

    driver = webdriver.Chrome(options=chrome_options)
    driver.set_window_size(1920, 1080)
    driver.get("https://dg18.co/wap/")
    time.sleep(10)  # 等待页面加载

    screenshot_path = "dg_screenshot.png"
    driver.save_screenshot(screenshot_path)
    driver.quit()
    return screenshot_path

def match_template(image_path, template_path, threshold=0.8):
    """模板匹配，返回匹配结果（True/False）"""
    img = cv2.imread(image_path, 0)
    template = cv2.imread(template_path, 0)
    if img is None or template is None:
        return False

    res = cv2.matchTemplate(img, template, cv2.TM_CCOEFF_NORMED)
    _, max_val, _, _ = cv2.minMaxLoc(res)
    return max_val >= threshold

def analyze_dg_platform():
    """分析DG平台截图，判断当前时段类型"""
    screenshot = open_dg_and_screenshot()

    fangshui_templates = [os.path.join(TEMPLATES_PATH, "fangshui", f) for f in os.listdir(os.path.join(TEMPLATES_PATH, "fangshui"))]
    medium_high_templates = [os.path.join(TEMPLATES_PATH, "medium_high", f) for f in os.listdir(os.path.join(TEMPLATES_PATH, "medium_high"))]
    shouge_templates = [os.path.join(TEMPLATES_PATH, "shouge", f) for f in os.listdir(os.path.join(TEMPLATES_PATH, "shouge"))]

    fangshui_count = sum(match_template(screenshot, t) for t in fangshui_templates)
    medium_high_count = sum(match_template(screenshot, t) for t in medium_high_templates)
    shouge_count = sum(match_template(screenshot, t) for t in shouge_templates)

    # 判断逻辑
    total_templates = fangshui_count + medium_high_count + shouge_count
    if fangshui_count >= 3 or (total_templates > 0 and fangshui_count / total_templates >= 0.7):
        return "fangshui"
    elif total_templates > 0 and 0.55 <= fangshui_count / total_templates < 0.7:
        return "medium_high"
    elif shouge_count > fangshui_count:
        return "shouge"
    else:
        return "medium"

def main():
    current_time = datetime.now(tz)
    status, start_time_str = load_status()
    start_time = datetime.fromisoformat(start_time_str) if start_time_str else None

    new_status = analyze_dg_platform()

    if new_status == "fangshui":
        if status != "fangshui":
            start_time = current_time
            send_telegram(
                f"🔥 {current_time.strftime('%Y-%m-%d %H:%M:%S')}\n"
                f"检测到【放水时段（提高胜率）】！\n请立即留意走势。"
            )
        save_status("fangshui", start_time.isoformat())

    elif new_status == "medium_high":
        if status != "medium_high":
            send_telegram(
                f"⚠ {current_time.strftime('%Y-%m-%d %H:%M:%S')}\n"
                f"检测到【类似放水时段（中等胜率中上）】。\n请注意观察。"
            )
        save_status("medium_high")

    else:
        if status == "fangshui" and start_time:
            duration = int((current_time - start_time).total_seconds() / 60)
            send_telegram(
                f"🔴 {current_time.strftime('%Y-%m-%d %H:%M:%S')}\n"
                f"放水已结束，共持续 {duration} 分钟。"
            )
        save_status(new_status)

if __name__ == "__main__":
    main()
