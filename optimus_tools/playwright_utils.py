import os
import json
import time
import logging
import random
import math

# 设置模块级 logger
logger = logging.getLogger(__name__)
def save_cookies(context, username, output_dir):
    filename = os.path.join(output_dir, "cookies", f"{username}_cookies.json")
    os.makedirs(os.path.dirname(filename), exist_ok=True)  # 👈 新增
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

def wait_cloudflare(page, timeout=180):
    """
    等待 Cloudflare 人机验证/自检页面结束。
    成功返回 True，超时返回 False。
    """
    keywords = [
        "请完成以下操作",
        "正在验证您是否是真人",
        "需要先检查您的连接的安全性"
    ]
    start = time.time()
    while time.time() - start < timeout:
        html = page.content()
        if not any(k in html for k in keywords):
            return True
        time.sleep(1)
    return False



def human_behavior(page=None, min_sec=2, max_sec=5, mouse_move=True, scroll=True):
    """
    模拟真人行为，包括随机等待、鼠标移动和页面滚动
    
    参数:
    - page: Playwright页面对象，如果传入则执行鼠标移动和页面滚动
    - min_sec: 最小等待秒数
    - max_sec: 最大等待秒数
    - mouse_move: 是否模拟鼠标移动
    - scroll: 是否模拟页面滚动
    """
    # 基础等待时间
    total_wait_time = random.uniform(min_sec, max_sec)
    
    # 如果没有提供页面对象或不需要模拟鼠标移动和滚动，只进行等待
    if not page or (not mouse_move and not scroll):
        time.sleep(total_wait_time)
        return
    
    # 获取页面尺寸
    viewport_size = page.viewport_size
    if not viewport_size:
        time.sleep(total_wait_time)
        return
        
    width, height = viewport_size["width"], viewport_size["height"]
    
    # 决定交互次数（2-5次）
    interaction_count = random.randint(2, 5)
    time_per_interaction = total_wait_time / interaction_count
    
    for i in range(interaction_count):
        # 每次交互随机选择行为：鼠标移动、滚动或两者都做
        do_mouse = mouse_move and random.random() < 0.7  # 70%概率移动鼠标
        do_scroll = scroll and random.random() < 0.5  # 50%概率滚动页面
        
        interaction_start = time.time()
        
        # 模拟鼠标移动
        if do_mouse:
            # 生成随机起点和终点
            start_x, start_y = random.randint(50, width-100), random.randint(50, height-100)
            end_x, end_y = random.randint(50, width-100), random.randint(50, height-100)
            
            # 随机决定鼠标轨迹复杂度（简单直线或贝塞尔曲线）
            if random.random() < 0.3:  # 30%概率使用简单直线
                steps = random.randint(5, 15)
                for j in range(steps + 1):
                    t = j / steps
                    x = start_x + (end_x - start_x) * t
                    y = start_y + (end_y - start_y) * t
                    page.mouse.move(x, y)
                    time.sleep(time_per_interaction / (steps * 3))
            else:  # 70%概率使用贝塞尔曲线
                # 贝塞尔曲线控制点数量
                num_points = random.randint(3, 6)
                
                # 随机中间控制点
                control_points = []
                for _ in range(num_points - 2):
                    cx = random.randint(0, width)
                    cy = random.randint(0, height)
                    control_points.append((cx, cy))
                
                # 生成贝塞尔曲线
                steps = random.randint(10, 20)  # 轨迹点数量
                for j in range(steps + 1):
                    t = j / steps
                    x, y = bezier_curve([start_x, *[p[0] for p in control_points], end_x], 
                                      [start_y, *[p[1] for p in control_points], end_y], t)
                    page.mouse.move(x, y)
                    
                    # 模拟人类鼠标速度变化：开始慢，中间快，结束慢
                    step_time = time_per_interaction / (steps * 3)
                    if j < steps * 0.3 or j > steps * 0.7:  # 开始和结束阶段移动慢
                        step_time *= 2
                    
                    time.sleep(step_time)
            
            # 随机在某个位置短暂停留
            if random.random() < 0.4:  # 40%概率停留
                time.sleep(random.uniform(0.1, 0.3))
        
        # 模拟页面滚动
        if do_scroll:
            # 随机决定滚动方向和距离
            scroll_distance = random.randint(50, 300) * (1 if random.random() < 0.7 else -1)
            
            # 使用JavaScript执行平滑滚动
            page.evaluate(f"""
                window.scrollBy({{
                    top: {scroll_distance},
                    left: 0,
                    behavior: 'smooth'
                }});
            """)
            
            # 滚动后短暂停留
            time.sleep(random.uniform(0.3, 0.7))
            
            # 偶尔进行连续滚动（更像人类阅读行为）
            if random.random() < 0.3:  # 30%概率连续滚动
                consecutive_scrolls = random.randint(1, 3)
                for _ in range(consecutive_scrolls):
                    time.sleep(random.uniform(0.3, 0.8))
                    second_scroll = random.randint(30, 150) * (1 if random.random() < 0.8 else -1)
                    page.evaluate(f"""
                        window.scrollBy({{
                            top: {second_scroll},
                            left: 0,
                            behavior: 'smooth'
                        }});
                    """)
        
        # 计算剩余时间并等待
        elapsed = time.time() - interaction_start
        remaining = time_per_interaction - elapsed
        if remaining > 0:
            time.sleep(remaining)
        
        # 偶尔模拟用户"思考"，即较长时间的停顿
        if i < interaction_count - 1 and random.random() < 0.2:  # 20%概率在交互之间有思考时间
            time.sleep(random.uniform(0.5, 1.5))

def bezier_curve(x_points, y_points, t):
    """计算贝塞尔曲线上的点"""
    n = len(x_points) - 1
    x = 0
    y = 0
    for i in range(n + 1):
        # 二项式系数
        coef = math.comb(n, i) * (t ** i) * ((1 - t) ** (n - i))
        x += coef * x_points[i]
        y += coef * y_points[i]
    return x, y

def random_sleep(min_sec=2, max_sec=5):
    """
    向后兼容的随机等待函数，内部调用human_behavior
    """
    human_behavior(None, min_sec, max_sec, False, False)