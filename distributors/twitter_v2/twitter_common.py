import re
from playwright.sync_api import Playwright, sync_playwright, expect
import time
import random
import json
import os
import sys
import pyotp
import math
from .config import get_twitter_config, get_proxy_config, get_browser_config, get_file_config, get_directories, get_cookies_file_path

# 从配置文件获取配置信息
twitter_config = get_twitter_config()
proxy_config = get_proxy_config()
browser_config = get_browser_config()
file_config = get_file_config()

USERNAME = twitter_config["USERNAME"]
EMAIL = twitter_config["EMAIL"]
PASSWORD = twitter_config["PASSWORD"]
TOTP_SECRET = twitter_config["TOTP_SECRET"]
PROXY = proxy_config["PROXY"]

def ensure_directories():
    """确保所有必要的目录存在"""
    directories = get_directories()
    for dir_name, dir_path in directories.items():
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
            print(f"📁 已创建目录: {dir_path}")

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
    try:
        viewport_size = page.viewport_size
        if not viewport_size:
            time.sleep(total_wait_time)
            return
    except Exception:
        # 页面可能已经被销毁，只进行等待
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
            try:
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
            except Exception:
                # 鼠标操作失败，跳过
                pass
        
        # 模拟页面滚动
        if do_scroll:
            try:
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
                        try:
                            page.evaluate(f"""
                                window.scrollBy({{
                                    top: {second_scroll},
                                    left: 0,
                                    behavior: 'smooth'
                                }});
                            """)
                        except Exception:
                            # 如果页面已经导航，跳过后续滚动
                            break
            except Exception:
                # 页面可能已经导航，跳过滚动操作
                pass
        
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

def save_cookies(context, username=None, filename=None):
    """保存 cookies 到文件，支持多账号"""
    if filename is None:
        filename = get_cookies_file_path(username)
    
    # 确保cookies目录存在
    cookies_dir = os.path.dirname(filename)
    if not os.path.exists(cookies_dir):
        os.makedirs(cookies_dir)
    
    cookies = context.cookies()
    with open(filename, "w") as f:
        json.dump(cookies, f)
    print(f"🍪 Cookies 已保存到 {filename}")

def load_cookies(context, username=None, filename=None):
    """从文件加载 cookies，支持多账号"""
    if filename is None:
        filename = get_cookies_file_path(username)
    
    try:
        with open(filename, "r") as f:
            cookies = json.load(f)
        context.add_cookies(cookies)
        print(f"🍪 已加载 Cookies 从 {filename}")
        return True
    except FileNotFoundError:
        print(f"🍪 未找到 Cookies 文件: {filename}")
        return False
    except Exception as e:
        print(f"❌ 加载 Cookies 时出错: {e}")
        return False

def login_with_credentials(page):
    """使用账号密码登录"""
    page.goto("https://x.com/i/flow/login")
    human_behavior(page)
    
    # 输入邮箱或用户名
    page.get_by_role("textbox", name="手机号码、邮件地址或用户名").fill(EMAIL)
    human_behavior(page)
    page.get_by_role("textbox", name="手机号码、邮件地址或用户名").press("Enter")
    human_behavior(page)
    
    # 如果出现需要输入用户名的情况
    if page.get_by_test_id("ocfEnterTextTextInput").is_visible():
        page.get_by_test_id("ocfEnterTextTextInput").click()
        human_behavior(page)
        page.get_by_test_id("ocfEnterTextTextInput").fill(USERNAME)
        human_behavior(page)
        page.get_by_test_id("ocfEnterTextTextInput").press("Enter")
        human_behavior(page)
    
    # 输入密码
    page.get_by_role("textbox", name="密码 显示密码").click()
    human_behavior(page)
    
    # 模拟人类输入密码的速度和节奏
    for char in PASSWORD:
        page.keyboard.type(char)
        time.sleep(random.uniform(0.05, 0.25))  # 每个字符之间的间隔时间
    
    human_behavior(page)
    page.get_by_test_id("LoginForm_Login_Button").click()
    human_behavior(page, 3, 6)
    
    # 使用pyotp生成验证码
    verification_code = pyotp.TOTP(TOTP_SECRET).now()
    print(f"生成的TOTP验证码: {verification_code}")
    
    # 输入验证码，模拟人类输入
    for char in verification_code:
        page.get_by_test_id("ocfEnterTextTextInput").focus()
        page.keyboard.type(char)
        time.sleep(random.uniform(0.1, 0.3))
        
    human_behavior(page)
    page.get_by_test_id("ocfEnterTextNextButton").click()
    human_behavior(page, 3, 5)
    
    # 登录成功后保存 cookies（使用当前用户名）
    save_cookies(page.context, USERNAME)

def setup_browser_and_login(playwright: Playwright):
    """
    设置浏览器并登录Twitter的公共函数
    
    参数:
    - playwright: Playwright对象
    
    返回:
    - tuple: (browser, context, page) 或 (None, None, None) 如果失败
    """
    try:
        # 设置浏览器启动选项，增加随机化特性以降低被识别风险
        browser_args = [
            '--disable-blink-features=AutomationControlled',
            f'--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_{random.randint(12, 15)}_{random.randint(1, 6)}) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{random.randint(90, 110)}.0.{random.randint(1000, 9999)}.{random.randint(100, 999)} Safari/537.36',
            '--window-size=1920,1080',
        ]
        
        browser = playwright.chromium.launch(headless=browser_config["HEADLESS"], channel="chrome", args=browser_args)
        context = browser.new_context(
            viewport=browser_config["VIEWPORT"],
            user_agent=browser_config["USER_AGENT"]
        )
        
        # 修改浏览器指纹信息以避免被检测
        context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => false
            });
            
            // 覆盖navigator属性
            const originalQuery = window.navigator.permissions.query;
            window.navigator.permissions.query = (parameters) => {
                if (parameters.name === 'notifications') {
                    return Promise.resolve({state: Notification.permission});
                }
                return originalQuery(parameters);
            };
            
            // 隐藏自动化相关特征
            delete window.cdc_adoQpoasnfa76pfcZLmcfl_Array;
            delete window.cdc_adoQpoasnfa76pfcZLmcfl_Promise;
            delete window.cdc_adoQpoasnfa76pfcZLmcfl_Symbol;
        """)
        
        page = context.new_page()
        
        # 尝试加载 cookies 并登录（使用当前用户名）
        cookies_loaded = load_cookies(context, USERNAME)
        
        if cookies_loaded:
            # 如果加载了 cookies，尝试访问 Twitter 主页
            page.goto("https://twitter.com/home")
            human_behavior(page)
            
            # 检查是否需要重新登录
            if page.url.startswith("https://twitter.com/i/flow/login"):
                print("Cookies 已过期，需要重新登录")
                login_with_credentials(page)
            else:
                print("使用 Cookies 成功登录")
        else:
            # 如果没有 cookies，使用账号密码登录
            login_with_credentials(page)
        
        print("✅ 浏览器设置和登录完成")
        return browser, context, page
        
    except Exception as e:
        print(f"❌ 浏览器设置或登录失败: {str(e)}")
        return None, None, None

def save_error_data(page, username, error_type):
    """
    保存错误数据，包括页面截图和HTML内容
    
    参数:
    - page: Playwright页面对象
    - username: 用户名
    - error_type: 错误类型描述
    """
    try:
        # 创建error_html文件夹(如果不存在)
        directories = get_directories()
        error_dir = directories["ERROR_HTML_DIR"]
        if not os.path.exists(error_dir):
            os.makedirs(error_dir)
            print(f"已创建{error_dir}文件夹")
        
        # 生成带有时间戳的文件名前缀
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        file_prefix = f"{error_dir}/{timestamp}_{username}_{error_type}"
        
        # 如果是回复按钮错误，添加高亮
        if error_type == "no_reply_button":
            # 尝试高亮所有可能的推文元素
            page.evaluate("""() => {
                try {
                    const tweets = document.querySelectorAll('article[data-testid="tweet"], article[role="article"], div[data-testid="tweet"]');
                    for (let tweet of tweets) {
                        tweet.style.border = '3px solid red';
                    }
                } catch (e) {
                    console.error('高亮推文元素失败', e);
                }
            }""")
        
        # 如果是图片上传相关错误，添加高亮
        if error_type.startswith("no_") and ("upload" in error_type or "attach" in error_type or "photo" in error_type):
            page.evaluate("""() => {
                try {
                    // 高亮工具栏
                    const toolBar = document.querySelector('[data-testid="toolBar"]');
                    if (toolBar) {
                        toolBar.style.border = '3px solid blue';
                    }
                    
                    // 高亮所有上传相关按钮
                    const buttons = document.querySelectorAll('button');
                    for (let button of buttons) {
                        const ariaLabel = button.getAttribute('aria-label') || '';
                        if (ariaLabel.toLowerCase().includes('photo') || 
                            ariaLabel.toLowerCase().includes('video') ||
                            ariaLabel.includes('照片') || 
                            ariaLabel.includes('视频')) {
                            button.style.border = '3px solid green';
                        }
                    }
                    
                    // 高亮文件输入框
                    const fileInputs = document.querySelectorAll('input[type="file"]');
                    for (let input of fileInputs) {
                        input.style.border = '3px solid orange';
                    }
                } catch (e) {
                    console.error('高亮上传元素失败', e);
                }
            }""")
        
        # 保存截图
        screenshot_path = f"{file_prefix}.png"
        page.screenshot(path=screenshot_path)
        print(f"已保存页面截图到: {screenshot_path}")
        
        # 保存完整的HTML内容
        html_path = f"{file_prefix}.html"
        html_content = page.content()
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        print(f"已保存HTML内容到: {html_path}")
        
        # 保存页面URL和当前时间
        info_path = f"{file_prefix}_info.txt"
        with open(info_path, 'w', encoding='utf-8') as f:
            f.write(f"错误类型: {error_type}\n")
            f.write(f"用户名: {username}\n")
            f.write(f"URL: {page.url}\n")
            f.write(f"时间: {timestamp}\n")
            f.write(f"User Agent: {page.evaluate('() => navigator.userAgent')}\n")
            f.write(f"Window Size: {page.evaluate('() => ({width: window.innerWidth, height: window.innerHeight})')}\n")
            
            # 尝试获取可见元素数量作为参考
            f.write(f"可见元素统计:\n")
            elements_stats = page.evaluate("""() => {
                const stats = {};
                stats.articles = document.querySelectorAll('article').length;
                stats.tweets = document.querySelectorAll('article[data-testid="tweet"]').length;
                stats.divs = document.querySelectorAll('div[data-testid="reply"]').length;
                stats.buttons = document.querySelectorAll('button[aria-label="Reply"], button[aria-label="回复"]').length;
                
                // 添加图片上传相关统计
                stats.toolBars = document.querySelectorAll('[data-testid="toolBar"]').length;
                stats.uploadButtons = document.querySelectorAll('button[aria-label*="photo"], button[aria-label*="video"]').length;
                stats.fileInputs = document.querySelectorAll('input[type="file"]').length;
                stats.mediaButtons = document.querySelectorAll('button[aria-label*="Add"]').length;
                
                return stats;
            }""")
            for key, value in elements_stats.items():
                f.write(f"  {key}: {value}\n")
        
        print(f"已保存调试信息到: {info_path}")
    
    except Exception as e:
        print(f"保存错误数据时出现问题: {str(e)}")



def handle_file_upload_dialog(page, image_paths=None, timeout=10000):
    """
    处理文件上传对话框
    
    参数:
    - page: Playwright页面对象
    - image_paths: 要上传的图片路径列表，如果为None则取消对话框
    - timeout: 等待对话框的超时时间（毫秒）
    
    返回:
    - bool: 是否成功处理
    """
    try:
        def handle_file_chooser(file_chooser):
            """处理文件选择器"""
            try:
                if image_paths and len(image_paths) > 0:
                    print(f"文件选择对话框已打开，准备上传 {len(image_paths)} 个文件")
                    file_chooser.set_files(image_paths)
                    print("文件已设置到选择器")
                else:
                    print("取消文件选择对话框")
                    # 通过设置空列表来取消选择
                    file_chooser.set_files([])
            except Exception as e:
                print(f"处理文件选择器时出错: {str(e)}")
        
        # 设置文件选择器监听器
        page.on("filechooser", handle_file_chooser)
        
        # 等待文件选择器事件或超时
        try:
            page.wait_for_event("filechooser", timeout=timeout)
            print("文件选择器事件已处理")
            return True
        except Exception as e:
            print(f"等待文件选择器超时或出错: {str(e)}")
            return False
        finally:
            # 移除监听器
            try:
                page.remove_listener("filechooser", handle_file_chooser)
            except:
                pass
                
    except Exception as e:
        print(f"处理文件上传对话框时出错: {str(e)}")
        return False

def cancel_file_upload_dialog(page):
    """
    取消文件上传对话框
    
    参数:
    - page: Playwright页面对象
    
    返回:
    - bool: 是否成功取消
    """
    try:
        # 尝试按ESC键取消对话框
        page.keyboard.press("Escape")
        print("已按ESC键尝试取消文件对话框")
        
        # 等待一下让对话框关闭
        time.sleep(1)
        
        # 也可以尝试点击页面其他地方来取消
        page.click("body")
        print("已点击页面其他区域尝试取消对话框")
        
        return True
    except Exception as e:
        print(f"取消文件上传对话框时出错: {str(e)}")
        return False 