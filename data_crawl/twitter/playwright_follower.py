from typing import List, Optional, Set
from playwright.sync_api import sync_playwright, Page
import logging
import os
import json
import math
import random
import time
from datetime import datetime
import sys
from optimus_tools.playwright_utils import save_cookies, load_cookies, save_error_data

# 从 play_twitter.py 导入复用函数
from data_crawl.twitter.play_twitter import (
    wait_cloudflare,
    human_behavior,
    bezier_curve,
    random_sleep
)

# 设置全局日志配置
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

# 主脚本 logger
logger = logging.getLogger(__name__)

class PlaywrightFollower:
    def __init__(
        self,
        username: str,
        password: str,
        totp_secret: str,
        proxy: Optional[str] = None,
        cookies_path: str = "./cookies.json",
        output_dir: str = ".",
        max_follows_per_session: int = 50
    ):
        """
        初始化PlaywrightFollower类
        
        Args:
            username: Twitter用户名
            password: Twitter密码
            proxy: 可选的代理服务器地址
            cookies_path: 用于保存/加载cookies的文件路径
            output_dir: 输出目录
            max_follows_per_session: 每个会话最大关注数量
        """
        self.username = username
        self.password = password
        self.totp_secret = totp_secret
        self.proxy = proxy
        self.cookies_path = cookies_path
        self.output_dir = output_dir
        self.max_follows_per_session = max_follows_per_session
        self.followed_users = set()
        self.page = None

    def login(self, page: Page) -> bool:
        """使用账号密码登录Twitter"""
        # 从 play_twitter.py 导入 login_with_credentials 函数
        from data_crawl.twitter.play_twitter import login_with_credentials
        
        try:
            # 尝试加载cookies
            if os.path.exists(self.cookies_path):
                logger.info(f"尝试从 {self.cookies_path} 加载cookies...")
                # 获取context从page
                context = page.context
                # 加载cookies需要context, username和output_dir参数
                if load_cookies(context, self.username, self.output_dir):
                    logger.info("已加载cookies，尝试直接访问主页")
                    page.goto("https://x.com/home")
                    human_behavior(page)
                    current_url = page.url
                    logger.info(f"当前URL: {current_url}")
                    if "home" in current_url:
                        logger.info("cookies有效，已登录")
                        return True
                    else:
                        logger.warning(f"cookies可能已失效，URL不匹配: {current_url}")
                else:
                    logger.warning("加载cookies失败，将使用账号密码登录")
            else:
                logger.info("未找到cookies文件，将使用账号密码登录")

            logger.info("开始使用账号密码登录...")
            # 调用同步的 login_with_credentials 函数
            login_with_credentials(
                page=page,
                username=self.username,
                password=self.password,
                totp_secret=self.totp_secret,
                output_dir=self.output_dir
            )
            
            logger.info("登录流程完成")
                
            return True

        except Exception as e:
            logger.error(f"登录失败: {str(e)}")
            return False



    def follow_user(self, username: str) -> bool:
        """关注指定用户"""
        try:
            # 查找特定用户的关注按钮
            follow_button = self.page.query_selector(f"[data-testid='UserCell'] a[href='/{username}'] ~ div button:has(div > span > span:has-text('Follow'))")
            
            if not follow_button:
                logger.warning(f"用户 {username} 的关注按钮未找到")
                return False

            # 滚动到元素
            follow_button.scroll_into_view_if_needed()
            human_behavior(self.page, min_sec=1, max_sec=3)
            
            # 点击关注
            follow_button.click()
            human_behavior(self.page, min_sec=2, max_sec=5)
            
            # 检查是否关注成功（按钮文本变化）
            try:
                self.page.wait_for_selector(
                    f"[data-testid='UserCell'] a[href='/{username}'] ~ div button:has(div > span > span:has-text('Following'))",
                    timeout=5000
                )
                self.followed_users.add(username)
                logger.info(f"成功关注用户 {username}")
                return True
            except Exception as e:
                logger.warning(f"可能关注失败 @{username}: {str(e)}")
                return False

        except Exception as e:
            logger.error(f"关注用户 {username} 失败: {str(e)}")
            return False

    def follow_users_from_page(self, target_username: str, max_follows: int = 10) -> int:
        """从目标用户的关注者页面直接关注用户"""
        try:
            logger.info(f"正在访问 @{target_username} 的关注者页面...")
            self.page.goto(f"https://x.com/{target_username}/followers", wait_until="networkidle")
            
            # 等待页面主要内容加载
            logger.info("等待页面完全加载...")
            try:
                # 等待主内容区域
                self.page.wait_for_selector("main", state="visible", timeout=30000)
                
                # 等待用户卡片容器出现
                logger.info("等待用户卡片加载...")
                self.page.wait_for_selector("[data-testid='UserCell']", state="visible", timeout=30000)
                logger.info("用户卡片加载完成")
                
                # 滚动一下页面，确保内容加载
                self.page.evaluate("window.scrollBy(0, 500)")
                human_behavior(self.page, min_sec=2, max_sec=4)
                
            except Exception as e:
                logger.error(f"等待元素超时: {str(e)}")
                self.page.screenshot(path="debug_timeout.png")
                logger.info("已保存调试截图: debug_timeout.png")
                return 0
            
            followed_count = 0
            last_position = 0
            max_scroll_attempts = 5
            scroll_attempts = 0
            processed_usernames = set()
            
            while followed_count < max_follows and scroll_attempts < max_scroll_attempts:
                # 获取当前页面上所有的用户卡片
                user_cells = self.page.query_selector_all("[data-testid='UserCell']")
                logger.info(f"找到 {len(user_cells)} 个用户卡片")
                
                if not user_cells:
                    logger.warning("没有找到用户卡片，尝试滚动...")
                    self.page.evaluate("window.scrollBy(0, window.innerHeight)")
                    human_behavior(self.page, min_sec=2, max_sec=4)
                    scroll_attempts += 1
                    continue
                
                new_users_found = False
                
                for i in range(last_position, len(user_cells)):
                    if followed_count >= max_follows:
                        break
                    
                    username = ""
                    try:
                        # 获取用户卡片中的用户名
                        user_link = user_cells[i].query_selector("a[href^='/']")
                        if not user_link:
                            logger.debug(f"未找到用户链接，跳过第 {i} 个用户卡片")
                            continue
                            
                        href = user_link.get_attribute('href')
                        if not href:
                            logger.debug(f"用户链接没有 href 属性，跳过")
                            continue
                            
                        username = href.lstrip('/')
                        
                        # 跳过已经处理过的用户
                        if username in processed_usernames:
                            logger.debug(f"用户 @{username} 已处理，跳过")
                            continue
                            
                        processed_usernames.add(username)
                        new_users_found = True
                        
                    except Exception as e:
                        logger.warning(f"处理用户卡片时出错: {str(e)}")
                        continue
                        
                    # 尝试找到关注按钮
                    follow_button = user_cells[i].query_selector("button:has(div > span > span:has-text('Follow'))")
                    if not follow_button:
                        logger.info(f"用户 @{username} 已关注或无法关注")
                        continue
                    
                    # 滚动到元素
                    try:
                        follow_button.scroll_into_view_if_needed()
                        human_behavior(self.page, min_sec=1, max_sec=3)
                        
                        # 点击关注
                        follow_button.click()
                        logger.info(f"正在关注 @{username}...")
                        human_behavior(self.page, min_sec=2, max_sec=5)
                        
                        # 检查是否关注成功 - 直接检查"Follow"按钮是否消失
                        try:
                            # 等待用户卡片加载
                            self.page.wait_for_selector(
                                f"[data-testid='UserCell'] a[href^='/{username}']",
                                state="attached",
                                timeout=5000
                            )
                            
                            # 检查"Follow"按钮是否消失
                            follow_btn = self.page.query_selector(
                                f"[data-testid='UserCell'] a[href^='/{username}'] "
                                "~ div button:has(div > span > span:has-text('Follow'))"
                            )
                            
                            if follow_btn:
                                # 如果按钮仍然存在，检查是否可点击
                                is_disabled = follow_btn.get_attribute('disabled') is not None
                                if not is_disabled:
                                    raise Exception("关注按钮仍然可点击，可能关注失败")
                                logger.debug(f"关注按钮存在但已禁用，可能正在处理中")
                                # 等待一段时间再检查一次
                                time.sleep(2)
                                follow_btn = self.page.query_selector(
                                    f"[data-testid='UserCell'] a[href^='/{username}'] "
                                    "~ div button:has(div > span > span:has-text('Follow'))"
                                )
                                if follow_btn and follow_btn.get_attribute('disabled') is None:
                                    raise Exception("关注按钮仍然可点击，关注失败")
                            
                            # 如果执行到这里，说明关注成功
                            followed_count += 1
                            logger.info(f"成功关注 @{username} (已关注: {followed_count}/{max_follows})")
                            
                            # 随机等待一段时间，模拟人类行为
                            human_behavior(self.page, min_sec=5, max_sec=15)
                            
                            # 每关注几个用户后随机滚动
                            if followed_count % 3 == 0:
                                scroll_distance = random.randint(300, 800)
                                self.page.evaluate(f"window.scrollBy(0, {scroll_distance})")
                                human_behavior(self.page, min_sec=1, max_sec=3)
                            
                            # 成功处理完一个用户，继续下一个
                            continue
                                
                        except Exception as e:
                            logger.warning(f"关注状态检查警告: {str(e)}")
                            # 检查失败时，可能关注成功也可能失败，这里保守处理，不增加计数
                            human_behavior(self.page, min_sec=5, max_sec=10)
                            
                    except Exception as e:
                        logger.error(f"关注 @{username} 时出错: {str(e)}")
                        # 出错时等待一段时间再继续
                        human_behavior(self.page, min_sec=3, max_sec=8)
                    
                    last_position = i + 1
                        
                # 如果没有找到新用户，尝试滚动加载更多
                if not new_users_found or len(user_cells) == last_position:
                    logger.info("没有新用户，尝试滚动加载更多...")
                    prev_height = self.page.evaluate("document.body.scrollHeight")
                    self.page.evaluate("window.scrollBy(0, window.innerHeight)")
                    
                    # 等待新内容加载
                    try:
                        self.page.wait_for_function(
                            f"document.body.scrollHeight > {prev_height}",
                            timeout=5000
                        )
                    except:
                        pass
                        
                    human_behavior(self.page, min_sec=2, max_sec=4)
                    scroll_attempts += 1
                else:
                    scroll_attempts = 0  # 重置滚动尝试计数
                    
                # 随机等待
                human_behavior(self.page, min_sec=2, max_sec=5)
                
            logger.info(f"本次共关注了 {followed_count} 个用户")
            return followed_count
            
        except Exception as e:
            logger.error(f"关注用户时出错: {str(e)}")
            return 0
            logger.info(f"本次共关注了 {followed_count} 个用户")
            return followed_count

        except Exception as e:
            logger.error(f"批量关注失败: {str(e)}")
            return 0

    def run(self, target_username: str):
        """运行关注流程"""
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=False)
            context = browser.new_context(proxy={"server": self.proxy} if self.proxy else None)
            self.page = context.new_page()

            try:
                # 登录
                if not self.login(self.page):
                    raise Exception("登录失败")

                # 开始关注流程
                followed_count = self.follow_users_from_page(target_username, self.max_follows_per_session)
                logger.info(f"任务完成，共关注了 {followed_count} 个用户")

            except Exception as e:
                logger.error(f"运行过程中出现错误: {str(e)}")
                raise
            finally:
                # 关闭浏览器
                browser.close()

def parse_args():
    parser = argparse.ArgumentParser(description="Twitter Follower Bot - Automatically follow followers of a target user")
    
    # Required arguments
    parser.add_argument("-u", "--username", required=False, help="Twitter username or email")
    parser.add_argument("-p", "--password", required=False, help="Twitter password")
    parser.add_argument("-s", "--totp-secret", default="UW2BOS4YH7M3HNZP", help="TOTP secret for 2FA")

    parser.add_argument("-t", "--target", required=True, help="Target username whose followers to follow")
    
    # Optional arguments
    parser.add_argument("--proxy", help="Proxy server (e.g., http://your_proxy:port)")
    parser.add_argument("--cookies-path", default="./cookies.json", 
                       help="Path to save/load cookies (default: ./cookies.json)")
    parser.add_argument("--output-dir", default="./outputs/comments", 
                       help="Output directory for logs and data (default: current directory)")
    parser.add_argument("--max-follows", type=int, default=50,
                       help="Maximum number of users to follow in one session (default: 50)")
    
    return parser.parse_args()

def main():
    args = parse_args()
    
    # 创建并运行
    follower = PlaywrightFollower(
        username=args.username,
        password=args.password,
        totp_secret=args.totp_secret,
        proxy=args.proxy,
        cookies_path=args.cookies_path,
        output_dir=args.output_dir,
        max_follows_per_session=args.max_follows
    )
    
    try:
        follower.run(args.target)
    except Exception as e:
        logger.error(f"An error occurred: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    import argparse
    import sys
    main()
