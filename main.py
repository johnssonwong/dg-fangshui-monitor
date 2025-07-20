import os
import requests
from datetime import datetime, timedelta
import pytz
import cv2
import numpy as np
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import time

# ===== Telegram 配置 =====
BOT_TOKEN = "8134230045:AAForY5xzO6D4EioSYNfk1yPtF6-cl50ABI"
CHAT_ID = "485427847"

# ===== 时区（马来西亚） =====
tz = pytz.timezone('Asia/Kuala_Lumpur')

# ===== 样本图路径 =====
TEMPLATE_PATHS = {
    "fangshui": "templates/fangshui/",
    "medium": "templates/medium/",
    "shouge": "templates/shouge/"
}

# ===== 状态缓存文件 =====
STATUS_FILE = "status_cache.txt"


# 发送 Telegram 消息
def send_telegram(message):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {"chat_id": CHAT_ID, "text": message}
    try:
        requests.post(url, data=data)
    except Exception as e:
        print(f"Telegram发送失败: {e}")


# 状态管理
def save_status(status, start_time=None):
    with open(STATUS_FILE, "w") as f:
        f.write(f"{status}|{start_time if start_time else ''}")


def load_status():
    if os.path.exists(STATUS_FILE):
        with open(STATUS_FILE, "r") as f:
            parts = f.read().split("|")
            return parts[0], parts[1] if len(parts) > 1 else ''
    return None, None


# 图像匹配
def match_template(screen, templates):
    screen_gray = cv2.cvtColor(screen, cv2.COLOR_BGR2GRAY)
    for tpl in templates:
        template = cv2.imread(tpl, 0)
        if template is None:
            continue
        res = cv2.matchTemplate(screen_gray, template, cv2.TM_CCOEFF_NORMED)
        if np.max(res) > 0.75:
            return True
    return False


# 加载样本图路径
def load_template_paths(folder):
    files = []
    if os.path.exists(folder):
        for f in os.listdir(folder):
            if f.lower().endswith((".jpg", ".png", ".jpeg")):
                files.append(os.path.join(folder, f))
    return files


# DG 平台检测逻辑
def analyze_dg_platform():
    options = Options()
    options.add_argument('--headless')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')
    driver = webdriver.Chrome(options=options)

    try:
        driver.get("https://dg18.co/wap/")
        time.sleep(5)

        # 模拟点击 “免费试玩” 或 “Free”
        try:
            free_btn = driver.find_element(By.PARTIAL_LINK_TEXT, "免费")
            free_btn.click()
            time.sleep(5)
        except:
            try:
                free_btn = driver.find_element(By.PARTIAL_LINK_TEXT, "Free")
                free_btn.click()
                time.sleep(5)
            except:
                pass

        # 截图当前页面
        screenshot_path = "current_screen.png"
        driver.save_screenshot(screenshot_path)

        # 加载截图
        screen = cv2.imread(screenshot_path)

        # 加载模板
        fangshui_templates = load_template_paths(TEMPLATE_PATHS["fangshui"])
        medium_templates = load_template_paths(TEMPLATE_PATHS["medium"])
        shouge_templates = load_template_paths(TEMPLATE_PATHS["shouge"])

        # 匹配逻辑
        if match_template(screen, fangshui_templates):
            return "fangshui"
        elif match_template(screen, medium_templates):
            return "medium_high"
        elif match_template(screen, shouge_templates):
            return "shouge"
        else:
            return "medium"

    except Exception as e:
        print(f"DG 检测错误: {e}")
        return "medium"

    finally:
        driver.quit()


# 主逻辑
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
                f"检测到【放水时段（提高胜率）】！\n预计持续 20-40 分钟，请留意走势。"
            )
        save_status("fangshui", start_time.isoformat())

    elif new_status == "medium_high":
        if status != "medium_high":
            send_telegram(
                f"⚠ {current_time.strftime('%Y-%m-%d %H:%M:%S')}\n"
                f"检测到【类似放水时段（中等胜率中上）】。\n请留意走势。"
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
