import re
from playwright.sync_api import Playwright, sync_playwright, expect
import time
import random
import json
import os
import sys
import pyotp
import math
import argparse
from optimus_tools.playwright_utils import save_cookies, load_cookies, save_error_data
import logging

# 设置全局日志配置
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

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


def login_with_credentials(page, username, password, totp_secret, output_dir):
    """使用账号密码登录"""
    page.goto("https://x.com/i/flow/login")
    human_behavior(page)

    # 输入邮箱或用户名
    page.get_by_role("textbox", name="手机号码、邮件地址或用户名").fill(username)
    human_behavior(page)
    page.get_by_role("textbox", name="手机号码、邮件地址或用户名").press("Enter")
    human_behavior(page)

    # 如果出现需要输入用户名的情况
    if page.get_by_test_id("ocfEnterTextTextInput").is_visible():
        page.get_by_test_id("ocfEnterTextTextInput").click()
        human_behavior(page)
        page.get_by_test_id("ocfEnterTextTextInput").fill(username)
        human_behavior(page)
        page.get_by_test_id("ocfEnterTextTextInput").press("Enter")
        human_behavior(page)

    # 输入密码
    page.get_by_role("textbox", name="密码 显示密码").click()
    human_behavior(page)

    # 模拟人类输入密码的速度和节奏
    for char in password:
        page.keyboard.type(char)
        time.sleep(random.uniform(0.05, 0.25))  # 每个字符之间的间隔时间

    human_behavior(page)
    page.get_by_test_id("LoginForm_Login_Button").click()
    human_behavior(page, 3, 6)

    # 使用pyotp生成验证码
    verification_code = pyotp.TOTP(totp_secret).now()
    logger.info(f"生成的TOTP验证码: {verification_code}")

    # 输入验证码，模拟人类输入
    for char in verification_code:
        page.get_by_test_id("ocfEnterTextTextInput").focus()
        page.keyboard.type(char)
        time.sleep(random.uniform(0.1, 0.3))

    human_behavior(page)
    page.get_by_test_id("ocfEnterTextNextButton").click()
    human_behavior(page, 3, 5)

    # 登录成功后保存 cookies
    save_cookies(page.context, username, output_dir)

def post_comment(page, username, comment_text, output_dir="."):
    """
    访问指定用户的主页并在其第一条推文下发表评论
    
    参数:
    - page: Playwright页面对象
    - username: 要访问的用户名(不带@)
    - comment_text: 评论内容
    
    返回:
    - bool: 评论是否成功
    """
    logger.info(f"正在访问用户 {username} 的主页...")
    
    try:
        # 访问用户主页
        page.goto(f"https://twitter.com/{username}")
        human_behavior(page, 5, 8, True, True)  # 增加等待时间
        
        # 查找第一条推文 - 尝试多种可能的选择器
        first_tweet = None
        tweet_selectors = [
            "article[data-testid='tweet']",
            "article[role='article']",
            "div[data-testid='tweet']",
            "div[data-testid='cellInnerDiv'] article",
            "div[role='region'] article"
        ]
        
        for selector in tweet_selectors:
            temp_tweet = page.locator(selector).first
            if temp_tweet and temp_tweet.is_visible():
                first_tweet = temp_tweet
                logger.info(f"找到第一条推文：{selector}")
                break
        
        if not first_tweet:
            logger.info(f"无法在 {username} 的主页上找到推文")
            save_error_data(page, username, output_dir, "no_tweet_found")
            return False
        
        # 查找回复按钮 - 使用更新的选择器并增加等待时间
        human_behavior(page, 5, 10, True, False)
        
        # 直接使用JavaScript查找和点击回复按钮
        reply_clicked = False  # 初始化变量
        reply_button = None
        if not reply_button:
            try:
                # 尝试使用JavaScript查找各种可能的回复按钮
                found = page.evaluate("""(tweetSelector) => {
                    const tweet = document.querySelector(tweetSelector);
                    if (!tweet) return false;
                    
                    // 尝试各种可能的回复按钮选择器
                    const possibleSelectors = [
                        'div[data-testid="reply"]',
                        'div[aria-label="Reply"]', 
                        'div[aria-label="回复"]',
                        'button[aria-label="Reply"]',
                        'button[aria-label="回复"]'
                    ];
                    
                    for (const selector of possibleSelectors) {
                        const replyButton = tweet.querySelector(selector);
                        if (replyButton) {
                            // 尝试点击找到的按钮
                            replyButton.click();
                            console.log('JavaScript找到并点击了回复按钮:', selector);
                            return true;
                        }
                    }
                    
                    // 查找所有可能与回复相关的元素
                    const allElements = tweet.querySelectorAll('*');
                    for (const el of allElements) {
                        const text = (el.textContent || '').toLowerCase();
                        const ariaLabel = (el.getAttribute('aria-label') || '').toLowerCase();
                        
                        if ((text.includes('reply') || text.includes('回复')) || 
                            (ariaLabel.includes('reply') || ariaLabel.includes('回复'))) {
                            console.log('通过文本内容找到了可能的回复按钮');
                            el.click();
                            return true;
                        }
                    }
                    
                    return false;
                }""", tweet_selectors[0])  # 使用找到推文的选择器
                
                if found:
                    logger.info("通过JavaScript成功找到并点击了回复按钮")
                    human_behavior(page, 2, 3)
                    # 不再需要点击reply_button，因为JavaScript已经点击了
                    reply_clicked = True
                else:
                    logger.info("JavaScript也无法找到回复按钮")
                    save_error_data(page, username, output_dir, "no_reply_button_js")
                    return False
            except Exception as e:
                logger.info(f"JavaScript查找回复按钮时出错: {str(e)}")
                # 继续使用常规方法
        
        # 检查回复按钮状态
        if not reply_button and not reply_clicked:
            logger.info(f"找不到回复按钮")
            save_error_data(page, username, output_dir, "no_reply_button")
            return False
            
        # 常规点击方法（如果JavaScript没有点击）
        if reply_button and not reply_clicked:
            reply_button.click()
            human_behavior(page, 1, 2)
        
        # 在回复框中输入评论内容 - 使用更新的选择器
        comment_box_selectors = [
            "div[data-testid='tweetTextarea_0']",
            "div[role='textbox']",
            "div[contenteditable='true']"
        ]
        
        comment_box = None
        for selector in comment_box_selectors:
            temp_box = page.locator(selector).first
            if temp_box and temp_box.is_visible():
                comment_box = temp_box
                logger.info(f"找到评论框：{selector}")
                break

        if not comment_box:
            logger.info("找不到评论输入框")
            save_error_data(page, username, output_dir, "no_comment_box")
            return False
            
        comment_box.click()
        human_behavior(page, 1, 2)
        
        # 模拟人类输入
        for word in comment_text.split():
            page.keyboard.type(word)
            page.keyboard.type(" ")
            time.sleep(random.uniform(0.2, 0.5))
        
        # 点击回复按钮发送评论 - 使用更新的选择器
        reply_send_button_selectors = [
            "div[data-testid='tweetButton']",
            "button[data-testid='tweetButton']",
            "button[data-testid='tweetButtonInline']",
            "div[role='button'][data-testid='tweetButton']",
            "button[aria-label='Reply']",
            "button[aria-label='回复']"
        ]
        
        reply_send_button = None
        for selector in reply_send_button_selectors:
            temp_button = page.locator(selector).first
            if temp_button and temp_button.is_visible():
                reply_send_button = temp_button
                break
        
        # 点击发送按钮
        if reply_send_button and reply_send_button is not True:
            logger.info("找到发送按钮并点击")
            reply_send_button.click()
        else:
            logger.info("找不到发送按钮")
            save_error_data(page, username, output_dir, "no_send_button")
            return False
        
        # 等待评论发送完成
        human_behavior(page, 3, 5)
        
        # 检查是否有成功发送的提示
        success = True  # 默认假设成功
        
        if success:
            logger.info(f"成功对 {username} 的推文发表评论")
        else:
            logger.info(f"评论可能未成功发送")
            save_error_data(page, username, output_dir, "send_failed")
            
        return success
        
    except Exception as e:
        logger.info(f"在 {username} 的主页发表评论时出错: {str(e)}")
        save_error_data(page, username, output_dir, f"exception_{str(e).replace(' ', '_')[:30]}")
        return False

def post_comments_to_users(page, users_list, comment_text_list, output_dir="."):
    """
    对用户列表中的每个用户的第一条推文发表评论
    
    参数:
    - page: Playwright页面对象
    - users_list: 用户名列表
    - comment_text: 评论内容
    """
    success_count = 0
    fail_count = 0
    
    for username in users_list:
        comment_text = random.choice(comment_text_list)
        try:
            logger.info(f"准备对用户 {username} 发表评论...")
            success = post_comment(page, username, comment_text, output_dir)
            if success:
                success_count += 1
                logger.info(f"成功评论 {username} 的推文 ({success_count}/{len(users_list)})")
                human_behavior(page, 20, 40, True, True)
            else:
                fail_count += 1
                logger.info(f"评论 {username} 的推文失败 ({fail_count} 失败)")
            human_behavior(page, 5, 15, True, True)
        except Exception as e:
            fail_count += 1
            logger.info(f"处理用户 {username} 时出错: {e}")
            human_behavior(page, 5, 10)
    logger.info(f"评论任务完成: 成功 {success_count}, 失败 {fail_count}")


def run(playwright: Playwright, args) -> None:
    # extract configuration
    username = args.username
    password = args.password
    totp_secret = args.totp_secret
    proxy = args.proxy
    target_users=args.target_users
    comment_text=args.comment_text
    output_dir = args.output_dir
    headless = args.headless

    # 设置浏览器启动选项，增加随机化特性以降低被识别风险
    browser_args = [
        '--disable-blink-features=AutomationControlled',
        f'--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_{random.randint(12, 15)}_{random.randint(1, 6)}) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{random.randint(90, 110)}.0.{random.randint(1000, 9999)}.{random.randint(100, 999)} Safari/537.36',
        '--window-size=1920,1080',
    ]
    browser = playwright.chromium.launch(
        headless=headless,
        channel="chrome",
        args=browser_args,
        proxy={"server": proxy} if proxy else None
    )
    context = browser.new_context(
        viewport={'width': 1366, 'height': 768},
        user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36'
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

    # login or reuse cookies
    if not load_cookies(context, username, output_dir):
        login_with_credentials(page, username, password, totp_secret, output_dir)
    else:
        page.goto("https://twitter.com/home")
        if page.url.startswith("https://twitter.com/i/flow/login"):
            login_with_credentials(page, username, password, totp_secret, output_dir)

    # 若遇到 Cloudflare 验证，则等待通过
    if not wait_cloudflare(page, 180):
        logger.info("⚠️ Cloudflare 验证仍未通过，脚本终止")
        context.close()
        browser.close()
        return

    human_behavior(page, 3, 6, True, True)
    post_comments_to_users(page, target_users, comment_text, output_dir)
    context.close()
    browser.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Playwright Twitter commenter")
    parser.add_argument("--username", default="Lucia6600537973", help="Twitter username or email")
    parser.add_argument("--password", default="N3MWIL82mP", help="Twitter password")
    parser.add_argument("--totp-secret", default="UW2BOS4YH7M3HNZP", help="TOTP secret for 2FA")
    parser.add_argument("--proxy", default="http://127.0.0.1:4780", help="HTTP/S or SOCKS5 proxy URL")
    parser.add_argument("--comment-text", type=str, default="w", help="Text to use for the comment")
    parser.add_argument("--target_users", nargs="+", default=["elonmusk", "lblpi61994842"], help="List of usernames to comment on")
    parser.add_argument("--headless", action="store_true", help="Run browser in headless mode")
    parser.add_argument("--output-dir", default="./outputs/comments", help="Directory for cookies, logs and outputs")
    args = parser.parse_args()
    with sync_playwright() as playwright:
        run(playwright, args)
