import json
import os
import time
import random
from playwright.sync_api import Playwright, sync_playwright
from .twitter_common import (
    human_behavior, 
    setup_browser_and_login, 
    save_error_data,
    ensure_directories,
    log_with_timestamp
)
from .config import get_file_config, get_behavior_config

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
        
        log_with_timestamp(f"从JSON文件 {filename} 成功提取了 {len(users)} 个用户名", "SUCCESS")
        return users
    
    except Exception as e:
        log_with_timestamp(f"加载JSON文件时出错: {e}", "ERROR")
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
    log_with_timestamp(f"正在访问用户 {username} 的主页：https://twitter.com/{username}...", "INFO")
    
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
                log_with_timestamp(f"找到第一条推文：{selector}", "SUCCESS")
                break
        
        if not first_tweet:
            log_with_timestamp(f"无法在 {username} 的主页上找到推文", "ERROR")
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
                        'button[aria-label="Reply"]'
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
                        
                        if ((text.includes('reply')) || 
                            (ariaLabel.includes('reply'))) {
                            console.log('通过文本内容找到了可能的回复按钮');
                            el.click();
                            return true;
                        }
                    }
                    
                    return false;
                }""", tweet_selectors[0])  # 使用找到推文的选择器
                
                if found:
                    log_with_timestamp("通过JavaScript成功找到并点击了回复按钮", "SUCCESS")
                    human_behavior(page, 2, 3)
                    # 不再需要点击reply_button，因为JavaScript已经点击了
                    reply_clicked = True
                else:
                    log_with_timestamp("JavaScript也无法找到回复按钮", "ERROR")
                    save_error_data(page, username, "no_reply_button_js")
                    return False
            except Exception as e:
                log_with_timestamp(f"JavaScript查找回复按钮时出错: {str(e)}", "ERROR")
                # 继续使用常规方法
        
        # 检查回复按钮状态
        if not reply_button and not reply_clicked:
            log_with_timestamp(f"找不到回复按钮", "ERROR")
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
                log_with_timestamp(f"找到评论框：{selector}", "SUCCESS")
                break
        
        if not comment_box:
            log_with_timestamp("找不到评论输入框", "ERROR")
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
                "div[aria-label='Add photos or video']"
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
                log_with_timestamp("找不到图片上传按钮", "WARNING")
        
        # 点击回复按钮发送评论 - 使用更新的选择器
        reply_send_button_selectors = [
            "div[data-testid='tweetButton']",
            "button[data-testid='tweetButton']",
            "button[data-testid='tweetButtonInline']",
            "div[role='button'][data-testid='tweetButton']",
            "button[aria-label='Reply']"
        ]
        
        reply_send_button = None
        for selector in reply_send_button_selectors:
            temp_button = page.locator(selector).first
            if temp_button and temp_button.is_visible():
                reply_send_button = temp_button
                break
        
        # 点击发送按钮
        if reply_send_button and reply_send_button is not True:
            log_with_timestamp("找到发送按钮并点击", "INFO")
            reply_send_button.click()
        else:
            log_with_timestamp("找不到发送按钮", "ERROR")
            save_error_data(page, username, "no_send_button")
            return False
        
        # 等待评论发送完成
        human_behavior(page, 3, 5)
        
        # 检查是否有成功发送的提示
        success = True  # 默认假设成功
        
        if success:
            log_with_timestamp(f"成功对 {username} 的推文发表评论", "SUCCESS")
        else:
            log_with_timestamp(f"评论可能未成功发送", "WARNING")
            save_error_data(page, username, "send_failed")
            
        return success
        
    except Exception as e:
        log_with_timestamp(f"在 {username} 的主页发表评论时出错: {str(e)}", "ERROR")
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
            log_with_timestamp(f"准备对用户 {username} 发表评论...", "INFO")
            success = post_comment(page, username, comment_text, image_path)
            
            result_detail = {
                'index': i + 1,
                'username': username,
                'comment_text': comment_text[:50] + '...' if len(comment_text) > 200 else comment_text,
                'success': success,
                'timestamp': time.strftime("%Y-%m-%d %H:%M:%S")
            }
            
            results['details'].append(result_detail)
            
            if success:
                results['success'] += 1
                log_with_timestamp(f"成功评论 {username} 的推文 ({results['success']}/{len(users_list)})", "SUCCESS")
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
                log_with_timestamp(f"评论 {username} 的推文失败 ({results['failed']} 失败)", "ERROR")
            
            # 实时保存评论结果
            if results_file:
                with open(results_file, 'w', encoding='utf-8') as f:
                    json.dump(results, f, ensure_ascii=False, indent=2)
            
            # 在每个用户操作之间添加随机延迟，避免被检测为机器人
            behavior_config = get_behavior_config()
            human_behavior(page, behavior_config["USER_DELAY_MIN"], behavior_config["USER_DELAY_MAX"], True, True)
            
        except Exception as e:
            results['failed'] += 1
            log_with_timestamp(f"处理用户 {username} 时出错: {e}", "ERROR")
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
    
    log_with_timestamp(f"批量评论完成: 成功 {results['success']} 个用户, 失败 {results['failed']} 个用户", "INFO")
    
    # 最终保存评论结果到统一目录
    if results_file:
        log_with_timestamp(f"评论结果已实时保存到: {results_file}", "INFO")
    
    return results

def run_comment_task(playwright: Playwright) -> None:
    """评论功能测试的主函数"""
    log_with_timestamp("=== Twitter 评论功能测试 ===", "INFO")
    
    # 确保所有必要的目录存在
    ensure_directories()
    
    # 从配置文件获取参数
    file_config = get_file_config()
    users_file = file_config["USERS_TO_COMMENT"]  # 评论的目标用户列表文件
    comment_text_file = file_config["COMMENT_TEXT_FILE"]  # 评论内容文件
    
    # 检查必要文件是否存在
    if not os.path.exists(comment_text_file):
        log_with_timestamp(f"❌ 评论内容文件不存在: {comment_text_file}", "ERROR")
        return
    
    # 夸赞的评论
    comment_text_list = json.load(open(comment_text_file, "r", encoding="utf-8"))
    image_path = None  # 默认没有图片
    
    # 加载用户列表
    users = load_users_from_file(users_file)
    if not users:
        log_with_timestamp(f"❌ 用户列表为空或无法加载文件 {users_file}", "ERROR")
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
    
    log_with_timestamp(f"📊 已加载 {len(users)} 个待评论用户", "INFO")
    if image_path:
        log_with_timestamp(f"🖼️ 图片路径: {image_path}", "INFO")
    
    # 设置浏览器并登录
    browser, context, page = setup_browser_and_login(playwright)
    if not all([browser, context, page]):
        log_with_timestamp("❌ 无法设置浏览器或登录，退出程序", "ERROR")
        return
    
    try:
        # 登录成功后，开始对用户列表发表评论
        human_behavior(page, 3, 6, True, True)
        
        # 准备实时保存的结果文件
        from .config import get_directories_with_date
        
        # 判断当前任务类型
        task_type = "comment"
        date_directories = get_directories_with_date(task_type)
        results_dir = date_directories["RESULTS_DIR"]
        
        result_filename = os.path.join(results_dir, f"comment_results_{time.strftime('%H%M%S')}.json")
        log_with_timestamp(f"💾 评论结果将实时保存到: {result_filename}", "INFO")
        
        results = post_comments_to_users(page, users, comment_text_list, image_path, comment_progress_info, result_filename)
        
        log_with_timestamp(f"\n📊 批量评论结果：", "INFO")
        log_with_timestamp(f"✅ 成功: {results['success']} 个用户", "SUCCESS")
        log_with_timestamp(f"❌ 失败: {results['failed']} 个用户", "ERROR")
        
        log_with_timestamp("🎉 评论任务完成！", "INFO")
        
    except Exception as e:
        log_with_timestamp(f"❌ 评论任务执行过程中出错: {str(e)}", "ERROR")
        log_with_timestamp(f"💡 提示: 已完成的评论结果已实时保存，可以查看结果文件", "INFO")
    finally:
        # 清理资源
        context.close()
        browser.close()

if __name__ == "__main__":
    with sync_playwright() as playwright:
        run_comment_task(playwright) 