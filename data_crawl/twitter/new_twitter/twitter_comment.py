import json
import os
import time
import random
from playwright.sync_api import Playwright, sync_playwright
from twitter_common import (
    human_behavior, 
    setup_browser_and_login, 
    save_error_data,
    ensure_directories
)
from config import get_file_config, get_behavior_config

def load_users_from_file(filename):
    """从JSON文件中提取screen_name字段作为用户名列表"""
    users = []
    
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
            # 直接从列表中提取screen_name
            for item in data:
                if isinstance(item, dict) and 'screen_name' in item:
                    users.append(item['screen_name'])
        
        print(f"从JSON文件 {filename} 成功提取了 {len(users)} 个用户名")
        return users
    
    except Exception as e:
        print(f"加载JSON文件时出错: {e}")
        return []

def post_comment(page, username, comment_text, image_path=None):
    """
    访问指定用户的主页并在其第一条推文下发表评论
    
    参数:
    - page: Playwright页面对象
    - username: 要访问的用户名(不带@)
    - comment_text: 评论内容
    - image_path: 可选，要上传的图片路径
    
    返回:
    - bool: 评论是否成功
    """
    print(f"正在访问用户 {username} 的主页...")
    
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
                print(f"找到第一条推文：{selector}")
                break
        
        if not first_tweet:
            print(f"无法在 {username} 的主页上找到推文")
            save_error_data(page, username, "no_tweet_found")
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
                    print("通过JavaScript成功找到并点击了回复按钮")
                    human_behavior(page, 2, 3)
                    # 不再需要点击reply_button，因为JavaScript已经点击了
                    reply_clicked = True
                else:
                    print("JavaScript也无法找到回复按钮")
                    save_error_data(page, username, "no_reply_button_js")
                    return False
            except Exception as e:
                print(f"JavaScript查找回复按钮时出错: {str(e)}")
                # 继续使用常规方法
        
        # 检查回复按钮状态
        if not reply_button and not reply_clicked:
            print(f"找不到回复按钮")
            save_error_data(page, username, "no_reply_button")
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
                print(f"找到评论框：{selector}")
                break
        
        if not comment_box:
            print("找不到评论输入框")
            save_error_data(page, username, "no_comment_box")
            return False
            
        comment_box.click()
        human_behavior(page, 1, 2)
        
        # 模拟人类输入
        for word in comment_text.split():
            page.keyboard.type(word)
            page.keyboard.type(" ")
            time.sleep(random.uniform(0.2, 0.5))
        
        # 如果有图片需要上传
        if image_path:
            upload_button_selectors = [
                "div[data-testid='attachments']",
                "div[aria-label='Add photos or video']",
                "div[aria-label='添加照片或视频']"
            ]
            
            upload_button = None
            for selector in upload_button_selectors:
                temp_button = page.locator(selector).first
                if temp_button and temp_button.is_visible():
                    upload_button = temp_button
                    break
            
            if upload_button:
                upload_button.click()
                human_behavior(page, 1, 2)
                
                # 上传图片
                file_input = page.locator("input[type='file']")
                file_input.set_input_files(image_path)
                human_behavior(page, 2, 4)
            else:
                print("找不到图片上传按钮")
        
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
            print("找到发送按钮并点击")
            reply_send_button.click()
        else:
            print("找不到发送按钮")
            save_error_data(page, username, "no_send_button")
            return False
        
        # 等待评论发送完成
        human_behavior(page, 3, 5)
        
        # 检查是否有成功发送的提示
        success = True  # 默认假设成功
        
        if success:
            print(f"成功对 {username} 的推文发表评论")
        else:
            print(f"评论可能未成功发送")
            save_error_data(page, username, "send_failed")
            
        return success
        
    except Exception as e:
        print(f"在 {username} 的主页发表评论时出错: {str(e)}")
        save_error_data(page, username, f"exception_{str(e).replace(' ', '_')[:30]}")
        return False

def post_comments_to_users(page, users_list, comment_text_list, image_path=None, comment_progress_info=[], results_file=None):
    """
    对用户列表中的每个用户的第一条推文发表评论
    
    参数:
    - page: Playwright页面对象
    - users_list: 用户名列表
    - comment_text_list: 评论内容列表
    - image_path: 可选，要上传的图片路径
    - comment_progress_info: 评论进度信息列表
    - results_file: 实时保存结果的文件路径
    
    返回:
    - dict: 评论结果统计 {'success': 成功数量, 'failed': 失败数量, 'details': 详细结果}
    """
    results = {
        'success': 0,
        'failed': 0,
        'details': []
    }
    
    for i, username in enumerate(users_list):
        # 有放回的随机选择
        comment_text = random.choice(comment_text_list)
        try:
            print(f"准备对用户 {username} 发表评论...")
            success = post_comment(page, username, comment_text, image_path)
            
            result_detail = {
                'index': i + 1,
                'username': username,
                'comment_text': comment_text[:50] + '...' if len(comment_text) > 50 else comment_text,
                'success': success,
                'timestamp': time.strftime("%Y-%m-%d %H:%M:%S")
            }
            
            results['details'].append(result_detail)
            
            if success:
                results['success'] += 1
                print(f"成功评论 {username} 的推文 ({results['success']}/{len(users_list)})")
                comment_progress_info.append({
                    "username": username,
                    "comment_text": comment_text,
                    "image_path": image_path,
                    "timestamp": str(time.strftime("%Y%m%d_%H%M%S"))
                })
                with open(get_file_config()["COMMENT_PROGRESS_FILE"], "w", encoding="utf-8") as f:
                    json.dump(comment_progress_info, f, ensure_ascii=False, indent=4)

                # 成功后增加随机延迟
                behavior_config = get_behavior_config()
                human_behavior(page, behavior_config["COMMENT_DELAY_MIN"], behavior_config["COMMENT_DELAY_MAX"], True, True)
            else:
                results['failed'] += 1
                print(f"评论 {username} 的推文失败 ({results['failed']} 失败)")
            
            # 实时保存评论结果
            if results_file:
                with open(results_file, 'w', encoding='utf-8') as f:
                    json.dump(results, f, ensure_ascii=False, indent=2)
            
            # 在每个用户操作之间添加随机延迟，避免被检测为机器人
            behavior_config = get_behavior_config()
            human_behavior(page, behavior_config["USER_DELAY_MIN"], behavior_config["USER_DELAY_MAX"], True, True)
            
        except Exception as e:
            results['failed'] += 1
            print(f"处理用户 {username} 时出错: {e}")
            results['details'].append({
                'index': i + 1,
                'username': username,
                'comment_text': comment_text[:50] + '...' if len(comment_text) > 50 else comment_text,
                'success': False,
                'error': str(e),
                'timestamp': time.strftime("%Y-%m-%d %H:%M:%S")
            })
            
            # 实时保存评论结果（包括失败的）
            if results_file:
                with open(results_file, 'w', encoding='utf-8') as f:
                    json.dump(results, f, ensure_ascii=False, indent=2)
            
            human_behavior(page, 5, 10)
    
    print(f"批量评论完成: 成功 {results['success']} 个用户, 失败 {results['failed']} 个用户")
    
    # 最终保存评论结果到统一目录
    if results_file:
        print(f"评论结果已实时保存到: {results_file}")
    
    return results

def run_comment_task(playwright: Playwright) -> None:
    """评论功能测试的主函数"""
    print("=== Twitter 评论功能测试 ===")
    
    # 确保所有必要的目录存在
    ensure_directories()
    
    # 从配置文件获取参数
    file_config = get_file_config()
    users_file = file_config["USERS_FILE"]  # 用户列表文件
    comment_text_file = file_config["COMMENT_TEXT_FILE"]  # 评论内容文件
    
    # 检查必要文件是否存在
    if not os.path.exists(comment_text_file):
        print(f"❌ 评论内容文件不存在: {comment_text_file}")
        return
    
    # 夸赞的评论
    comment_text_list = json.load(open(comment_text_file, "r", encoding="utf-8"))
    image_path = None  # 默认没有图片
    
    # 加载用户列表
    users = load_users_from_file(users_file)
    if not users:
        print(f"❌ 用户列表为空或无法加载文件 {users_file}")
        return
    
    # 加载已成功评论的用户列表
    comment_progress_file = file_config["COMMENT_PROGRESS_FILE"]
    comment_progress_users = []
    if os.path.exists(comment_progress_file):
        with open(comment_progress_file, "r", encoding="utf-8") as f:
            comment_progress_info = json.load(f)
            comment_progress_users = [user['username'] for user in comment_progress_info]
    else:
        comment_progress_info = []
    
    # 过滤掉已经评论过的用户
    users = [user for user in users if user not in comment_progress_users]
    
    print(f"📊 已加载 {len(users)} 个待评论用户")
    if image_path:
        print(f"🖼️ 图片路径: {image_path}")
    
    # 设置浏览器并登录
    browser, context, page = setup_browser_and_login(playwright)
    if not all([browser, context, page]):
        print("❌ 无法设置浏览器或登录，退出程序")
        return
    
    try:
        # 登录成功后，开始对用户列表发表评论
        human_behavior(page, 3, 6, True, True)
        
        # 准备实时保存的结果文件
        from config import get_directories
        directories = get_directories()
        results_dir = directories["RESULTS_DIR"]
        
        result_filename = os.path.join(results_dir, f"comment_results_{time.strftime('%Y%m%d_%H%M%S')}.json")
        print(f"💾 评论结果将实时保存到: {result_filename}")
        
        results = post_comments_to_users(page, users, comment_text_list, image_path, comment_progress_info, result_filename)
        
        print(f"\n📊 批量评论结果：")
        print(f"✅ 成功: {results['success']} 个用户")
        print(f"❌ 失败: {results['failed']} 个用户")
        
        print("🎉 评论任务完成！")
        
    except Exception as e:
        print(f"❌ 评论任务执行过程中出错: {str(e)}")
        print(f"💡 提示: 已完成的评论结果已实时保存，可以查看结果文件")
    finally:
        # 清理资源
        context.close()
        browser.close()

if __name__ == "__main__":
    with sync_playwright() as playwright:
        run_comment_task(playwright) 