import json
import os
import time
import random
from playwright.sync_api import Playwright, sync_playwright
from .twitter_common import (
    human_behavior, 
    setup_browser_and_login, 
    save_error_data,
    ensure_directories
)
from .config import get_behavior_config, get_file_config, get_directories

def load_target_users_from_file(filename):
    """从JSON文件中加载目标用户列表"""
    target_users = []
    
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
            # 验证数据格式
            if isinstance(data, list):
                for item in data:
                    if isinstance(item, dict) and 'username' in item:
                        target_users.append(item)
                    elif isinstance(item, str):
                        # 如果是字符串，转换为字典格式
                        target_users.append({'username': item, 'max_follows': 10})
                    else:
                        print(f"跳过无效的用户数据: {item}")
            else:
                print(f"用户文件格式错误，应该是一个列表")
                return []
        
        print(f"从JSON文件 {filename} 成功加载了 {len(target_users)} 个目标用户")
        return target_users
    
    except Exception as e:
        print(f"加载目标用户文件时出错: {e}")
        return []

def load_followed_users(filename):
    """加载已关注的用户记录"""
    followed_users = []
    
    try:
        if os.path.exists(filename):
            with open(filename, 'r', encoding='utf-8') as f:
                followed_users = json.load(f)
            print(f"📊 已加载 {len(followed_users)} 条已关注用户记录")
        else:
            print(f"📝 未找到已关注记录文件，将创建新文件: {filename}")
        
        return followed_users
    
    except Exception as e:
        print(f"⚠️ 加载已关注用户记录时出错: {e}")
        return []

def append_followed_user(filename, user_data):
    """追加单条已关注的用户记录"""
    try:
        existing_data = []
        
        # 如果文件存在，先读取现有数据
        if os.path.exists(filename):
            with open(filename, 'r', encoding='utf-8') as f:
                try:
                    existing_data = json.load(f)
                except json.JSONDecodeError:
                    existing_data = []
        
        # 添加新记录
        existing_data.append(user_data)
        
        # 保存到文件
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(existing_data, f, ensure_ascii=False, indent=4)
        
        return True
    
    except Exception as e:
        print(f"❌ 保存关注记录时出错: {e}")
        return False

def is_user_already_followed(username, followed_users):
    """检查用户是否已经关注过"""
    for followed in followed_users:
        if followed.get('username', '') == username:
            return True
    return False

def follow_user_on_page(page, username):
    """在当前页面关注指定用户"""
    try:
        print(f"尝试关注用户: @{username}")
        
        # 查找用户卡片中的关注按钮
        follow_button_selectors = [
            f"[data-testid='UserCell'] a[href='/{username}'] ~ div button:has(div > span > span:has-text('Follow'))",
            f"div[data-testid='UserCell'] button:has(span:has-text('Follow'))",
            "button[data-testid='follow']",
            "button:has(span:has-text('Follow'))",
            "div[role='button']:has(span:has-text('Follow'))"
        ]
        
        follow_button = None
        for selector in follow_button_selectors:
            try:
                temp_button = page.locator(selector).first
                if temp_button and temp_button.is_visible():
                    follow_button = temp_button
                    print(f"找到关注按钮: {selector}")
                    break
            except Exception:
                continue
        
        if not follow_button:
            print(f"未找到 @{username} 的关注按钮，可能已关注或用户不存在")
            return False
        
        # 滚动到按钮位置
        try:
            follow_button.scroll_into_view_if_needed()
            human_behavior(page, 1, 2)
        except Exception:
            pass
        
        # 点击关注按钮
        follow_button.click()
        print(f"已点击关注按钮")
        
        # 等待关注完成
        human_behavior(page, 2, 4)
        
        # 检查是否关注成功 - 查找Following按钮或关注按钮消失
        try:
            # 方法1: 查找Following按钮
            following_button = page.locator("button:has(span:has-text('Following'))").first
            if following_button and following_button.is_visible():
                print(f"成功关注 @{username} - 找到Following按钮")
                return True
            
            # 方法2: 检查Follow按钮是否消失或变为不可点击
            follow_buttons = page.locator("button:has(span:has-text('Follow'))").all()
            if len(follow_buttons) == 0:
                print(f"成功关注 @{username} - Follow按钮已消失")
                return True
            
            # 方法3: 检查按钮是否被禁用
            for fb in follow_buttons:
                if fb.is_disabled():
                    print(f"成功关注 @{username} - Follow按钮已禁用")
                    return True
            
            print(f"关注 @{username} 的状态不确定")
            return False
            
        except Exception as e:
            print(f"检查关注状态时出错: {str(e)}")
            return False
    
    except Exception as e:
        print(f"关注用户 @{username} 时出错: {str(e)}")
        save_error_data(page, "follow_user", f"follow_error_{username}")
        return False

def follow_users_from_target_page(page, target_username, max_follows=10, followed_progress_file=None):
    """
    从目标用户的关注者页面批量关注用户
    
    参数:
    - page: Playwright页面对象
    - target_username: 目标用户名（从其关注者中挑选用户关注）
    - max_follows: 最大关注数量
    - followed_progress_file: 关注进度记录文件路径
    
    返回:
    - int: 成功关注的用户数量
    """
    print(f"准备从 @{target_username} 的关注者中关注最多 {max_follows} 个用户")
    
    try:
        # 访问目标用户的关注者页面
        followers_url = f"https://twitter.com/{target_username}/followers"
        print(f"访问关注者页面: {followers_url}")
        page.goto(followers_url)
        human_behavior(page, 3, 5, True, True)
        
        # 等待页面加载
        try:
            page.wait_for_selector("[data-testid='UserCell']", timeout=30000)
            print("用户卡片加载完成")
        except Exception as e:
            print(f"等待用户卡片超时: {str(e)}")
            save_error_data(page, "follow_users", "user_cell_timeout")
            return 0
        
        # 滚动一下确保内容加载
        page.evaluate("window.scrollBy(0, 500)")
        human_behavior(page, 2, 3)
        
        followed_count = 0
        last_position = 0
        max_scroll_attempts = 5
        scroll_attempts = 0
        processed_usernames = set()
        
        while followed_count < max_follows and scroll_attempts < max_scroll_attempts:
            # 获取当前页面上所有的用户卡片
            user_cells = page.query_selector_all("[data-testid='UserCell']")
            print(f"找到 {len(user_cells)} 个用户卡片")
            
            if not user_cells:
                print("没有找到用户卡片，尝试滚动...")
                page.evaluate("window.scrollBy(0, window.innerHeight)")
                human_behavior(page, 2, 4)
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
                        continue
                        
                    href = user_link.get_attribute('href')
                    if not href:
                        continue
                        
                    username = href.lstrip('/')
                    
                    # 跳过已经处理过的用户
                    if username in processed_usernames:
                        continue
                        
                    processed_usernames.add(username)
                    new_users_found = True
                    
                except Exception as e:
                    print(f"获取用户名时出错: {str(e)}")
                    continue
                
                # 尝试找到关注按钮
                follow_button = user_cells[i].query_selector("button:has(div > span > span:has-text('Follow'))")
                if not follow_button:
                    print(f"用户 @{username} 已关注或无法关注")
                    continue
                
                # 尝试关注用户
                try:
                    # 滚动到元素
                    follow_button.scroll_into_view_if_needed()
                    human_behavior(page, 1, 2)
                    
                    # 点击关注
                    follow_button.click()
                    print(f"正在关注 @{username}...")
                    human_behavior(page, 2, 4)
                    
                    # 检查是否关注成功
                    success = False
                    try:
                        # 等待一下让页面更新
                        time.sleep(2)
                        
                        # 重新获取用户卡片
                        updated_user_cells = page.query_selector_all("[data-testid='UserCell']")
                        if i < len(updated_user_cells):
                            follow_btn_check = updated_user_cells[i].query_selector("button:has(div > span > span:has-text('Follow'))")
                            if not follow_btn_check:
                                success = True
                            else:
                                # 检查按钮是否被禁用
                                is_disabled = follow_btn_check.get_attribute('disabled') is not None
                                if is_disabled:
                                    success = True
                    except Exception:
                        # 如果检查失败，保守认为成功
                        success = True
                    
                    if success:
                        followed_count += 1
                        print(f"成功关注 @{username} (已关注: {followed_count}/{max_follows})")
                        
                        # 实时保存关注记录
                        if followed_progress_file:
                            followed_data = {
                                'username': username,
                                'target_user': target_username,
                                'timestamp': time.strftime("%Y-%m-%d %H:%M:%S")
                            }
                            append_followed_user(followed_progress_file, followed_data)
                        
                        # 随机等待
                        behavior_config = get_behavior_config()
                        delay_time = random.randint(behavior_config.get("FOLLOW_DELAY_MIN", 5), 
                                                 behavior_config.get("FOLLOW_DELAY_MAX", 15))
                        print(f"等待 {delay_time} 秒后继续...")
                        human_behavior(page, delay_time, delay_time + 5, True, True)
                    else:
                        print(f"关注 @{username} 可能失败")
                        human_behavior(page, 3, 6)
                        
                except Exception as e:
                    print(f"关注 @{username} 时出错: {str(e)}")
                    human_behavior(page, 3, 8)
                
                last_position = i + 1
            
            # 如果没有找到新用户，尝试滚动加载更多
            if not new_users_found or len(user_cells) == last_position:
                print("没有新用户，尝试滚动加载更多...")
                prev_height = page.evaluate("document.body.scrollHeight")
                page.evaluate("window.scrollBy(0, window.innerHeight)")
                
                # 等待新内容加载
                try:
                    page.wait_for_function(
                        f"document.body.scrollHeight > {prev_height}",
                        timeout=5000
                    )
                except:
                    pass
                    
                human_behavior(page, 2, 4)
                scroll_attempts += 1
            else:
                scroll_attempts = 0  # 重置滚动尝试计数
            
            # 随机等待
            human_behavior(page, 2, 4)
        
        print(f"从 @{target_username} 的关注者中成功关注了 {followed_count} 个用户")
        return followed_count
        
    except Exception as e:
        print(f"批量关注失败: {str(e)}")
        save_error_data(page, "follow_users", f"batch_follow_error")
        return 0

def run_follow_task(playwright: Playwright) -> None:
    """关注功能的主函数"""
    print("=== Twitter 批量关注功能 ===")
    
    # 确保所有必要的目录存在
    ensure_directories()
    
    # 从配置文件获取参数
    file_config = get_file_config()
    
    # 检查是否有目标用户文件配置
    target_users_file = file_config.get("TARGET_USERS_FILE")
    if not target_users_file:
        # 如果配置文件中没有，使用默认路径
        directories = get_directories()
        target_users_file = os.path.join(directories["DATA_DIR"], "target_users.json")
    
    follow_progress_file = file_config.get("FOLLOW_PROGRESS_FILE")
    if not follow_progress_file:
        # 如果配置文件中没有，使用默认路径
        directories = get_directories()
        follow_progress_file = os.path.join(directories["PROGRESS_DIR"], "follow_progress.json")
    
    # 检查必要文件是否存在
    if not os.path.exists(target_users_file):
        print(f"❌ 目标用户文件不存在: {target_users_file}")
        print("请创建目标用户文件，格式如下:")
        print("""[
    {"username": "user1", "max_follows": 10},
    {"username": "user2", "max_follows": 15}
]""")
        return
    
    # 加载目标用户列表
    target_users = load_target_users_from_file(target_users_file)
    if not target_users:
        print(f"❌ 目标用户列表为空或无法加载文件 {target_users_file}")
        return
    
    # 加载已关注的用户记录（断点恢复）
    followed_users = load_followed_users(follow_progress_file)
    
    print(f"📝 本次将处理 {len(target_users)} 个目标用户的关注者")
    
    # 设置浏览器并登录
    browser, context, page = setup_browser_and_login(playwright)
    if not all([browser, context, page]):
        print("❌ 无法设置浏览器或登录，退出程序")
        return
    
    try:
        # 登录成功后，开始批量关注
        human_behavior(page, 3, 6, True, True)
        
        total_followed = 0
        
        for i, target_user in enumerate(target_users):
            target_username = target_user.get('username', '')
            max_follows = target_user.get('max_follows', 10)
            
            if not target_username:
                print(f"跳过无效的目标用户: {target_user}")
                continue
            
            print(f"\n📤 处理第 {i+1}/{len(target_users)} 个目标用户: @{target_username}")
            print(f"⏱️ 计划关注最多 {max_follows} 个用户")
            
            # 从目标用户的关注者中关注用户
            followed_count = follow_users_from_target_page(
                page, 
                target_username, 
                max_follows, 
                follow_progress_file
            )
            
            total_followed += followed_count
            print(f"✅ 从 @{target_username} 成功关注了 {followed_count} 个用户")
            
            # 如果不是最后一个目标用户，添加延迟
            if i < len(target_users) - 1:
                behavior_config = get_behavior_config()
                user_delay = random.randint(
                    behavior_config.get("USER_DELAY_MIN", 30), 
                    behavior_config.get("USER_DELAY_MAX", 60)
                )
                print(f"等待 {user_delay} 秒后处理下一个目标用户...")
                human_behavior(page, user_delay, user_delay + 10, True, True)
        
        print(f"\n📊 批量关注结果：")
        print(f"✅ 总共成功关注: {total_followed} 个用户")
        print(f"🎉 关注任务完成！")
        
    except Exception as e:
        print(f"❌ 关注过程中出现错误: {str(e)}")
        print(f"💡 提示: 已成功关注的用户已保存，可以重新运行程序继续关注")
    finally:
        # 清理资源
        context.close()
        browser.close()

if __name__ == "__main__":
    with sync_playwright() as playwright:
        run_follow_task(playwright) 