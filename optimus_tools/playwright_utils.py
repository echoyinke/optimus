import os
import json
import time
import logging

# 设置模块级 logger
logger = logging.getLogger(__name__)
def save_cookies(context, username, output_dir):
    filename = os.path.join(output_dir, "cookies", f"{username}_cookies.json")
    cookies = context.cookies()
    with open(filename, "w") as f:
        json.dump(cookies, f)
    logger.info(f"Cookies 已保存到 {filename}")

def load_cookies(context, username, output_dir):
    filename = os.path.join(output_dir, "cookies", f"{username}_cookies.json")
    try:
        with open(filename, "r") as f:
            cookies = json.load(f)
        context.add_cookies(cookies)
        logger.info(f"已加载 Cookies 从 {filename}")
        return True
    except FileNotFoundError:
        logger.warning(f"未找到 Cookies 文件: {filename}")
        return False
    except Exception as e:
        logger.error(f"加载 Cookies 时出错: {e}")
        return False

def save_error_data(page, username, output_dir, error_type):
    try:
        error_dir = os.path.join(output_dir, "error_html")
        os.makedirs(error_dir, exist_ok=True)
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        file_prefix = os.path.join(error_dir, f"{timestamp}_{username}_{error_type}")

        if error_type == "no_reply_button":
            page.evaluate("""() => {
                const tweets = document.querySelectorAll('article[data-testid="tweet"], article[role="article"], div[data-testid="tweet"]');
                for (let tweet of tweets) {
                    tweet.style.border = '3px solid red';
                }
            }""")

        page.screenshot(path=f"{file_prefix}.png")
        with open(f"{file_prefix}.html", 'w', encoding='utf-8') as f:
            f.write(page.content())
        with open(f"{file_prefix}_info.txt", 'w', encoding='utf-8') as f:
            f.write(f"错误类型: {error_type}\n")
            f.write(f"用户名: {username}\n")
            f.write(f"URL: {page.url}\n")
            f.write(f"时间: {timestamp}\n")
            f.write(f"User Agent: {page.evaluate('() => navigator.userAgent')}\n")
            f.write(f"Window Size: {page.evaluate('() => ({width: window.innerWidth, height: window.innerHeight})')}\n")
    except Exception as e:
        logger.error(f"保存错误数据时出错: {str(e)}")