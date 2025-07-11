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
from .config import get_behavior_config, get_file_config

def load_tweet_content_from_file(filename):
    """从JSON文件中加载推文内容列表"""
    tweet_contents = []
    
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
            # 验证数据格式
            if isinstance(data, list):
                for item in data:
                    if isinstance(item, dict) and 'text' in item:
                        # 确保images字段存在，如果不存在则设为空列表
                        if 'images' not in item:
                            item['images'] = []
                        tweet_contents.append(item)
                    else:
                        print(f"跳过无效的推文数据: {item}")
            else:
                print(f"推文内容文件格式错误，应该是一个列表")
                return []
        
        print(f"从JSON文件 {filename} 成功加载了 {len(tweet_contents)} 条推文内容")
        return tweet_contents
    
    except Exception as e:
        print(f"加载推文内容文件时出错: {e}")
        return []

def load_published_tweets(filename):
    """加载已发布的推文记录"""
    published_tweets = []
    
    try:
        if os.path.exists(filename):
            with open(filename, 'r', encoding='utf-8') as f:
                published_tweets = json.load(f)
            print(f"📊 已加载 {len(published_tweets)} 条已发布推文记录")
        else:
            print(f"📝 未找到已发布记录文件，将创建新文件: {filename}")
        
        return published_tweets
    
    except Exception as e:
        print(f"⚠️ 加载已发布推文记录时出错: {e}")
        return []

def append_published_tweet(filename, tweet_data):
    """追加单条已发布的推文记录（避免重复加载）"""
    try:
        # 直接追加到现有文件，避免重复加载
        existing_data = []
        
        # 如果文件存在，先读取现有数据
        if os.path.exists(filename):
            with open(filename, 'r', encoding='utf-8') as f:
                try:
                    existing_data = json.load(f)
                except json.JSONDecodeError:
                    existing_data = []
        
        # 添加新记录
        existing_data.append(tweet_data)
        
        # 保存到文件
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(existing_data, f, ensure_ascii=False, indent=4)
        
        return True
    
    except Exception as e:
        print(f"❌ 保存发布记录时出错: {e}")
        return False

def is_tweet_already_published(tweet_data, published_tweets):
    """检查推文是否已经发布过（基于text + images组合）"""
    tweet_text = tweet_data.get('text', '').strip()
    tweet_images = tweet_data.get('images', [])
    
    # 标准化图片路径列表（排序后比较，避免顺序影响）
    tweet_images_sorted = sorted(tweet_images) if tweet_images else []
    
    for published in published_tweets:
        published_text = published.get('text', '').strip()
        published_images = published.get('images', [])
        published_images_sorted = sorted(published_images) if published_images else []
        
        # 同时比较文本和图片
        if (published_text == tweet_text and 
            published_images_sorted == tweet_images_sorted):
            return True
    
    return False

def filter_unpublished_tweets(tweet_contents, published_tweets):
    """过滤出未发布的推文内容"""
    unpublished = []
    
    for tweet in tweet_contents:
        if not is_tweet_already_published(tweet, published_tweets):
            unpublished.append(tweet)
        else:
            tweet_text = tweet.get('text', '')
            # print(f"⏭️ 跳过已发布的推文: {tweet_text[:50]}...")
    
    print(f"📋 过滤结果: 总共 {len(tweet_contents)} 条，已发布 {len(tweet_contents) - len(unpublished)} 条，待发布 {len(unpublished)} 条")
    return unpublished

def post_tweet(page, tweet_text, image_paths=None):
    """
    发布推文，支持文本和多张图片
    
    参数:
    - page: Playwright页面对象
    - tweet_text: 推文文本内容
    - image_paths: 图片路径列表，最多4张图片
    
    返回:
    - bool: 发布是否成功
    """
    print(f"准备发布推文: {tweet_text[:50]}...")
    
    try:
        # 访问Twitter主页
        page.goto("https://twitter.com/home")
        human_behavior(page, 3, 5, True, True)
        
        # 查找推文输入框 - 尝试多种可能的选择器
        tweet_box_selectors = [
            "div[data-testid='tweetTextarea_0']",
            "div[role='textbox'][data-testid='tweetTextarea_0']",
            "div[contenteditable='true'][data-testid='tweetTextarea_0']",
            "div[aria-label='Tweet text']"
        ]
        
        tweet_box = None
        for selector in tweet_box_selectors:
            temp_box = page.locator(selector).first
            if temp_box and temp_box.is_visible():
                tweet_box = temp_box
                print(f"找到推文输入框: {selector}")
                break
        
        if not tweet_box:
            print("找不到推文输入框")
            save_error_data(page, "post_tweet", "no_tweet_box")
            return False
        
        # 点击推文输入框并输入内容
        tweet_box.click()
        human_behavior(page, 1, 2)
        
        # 清空输入框（如果有内容）
        page.keyboard.press("Control+a")
        time.sleep(0.2)
        
        # 模拟人类输入推文内容
        words = tweet_text.split()
        for i, word in enumerate(words):
            page.keyboard.type(word)
            if i < len(words) - 1:  # 不是最后一个词时添加空格
                page.keyboard.type(" ")
            # 随机停顿，模拟思考
            if random.random() < 0.1:  # 10%概率停顿
                time.sleep(random.uniform(0.5, 1.5))
            else:
                time.sleep(random.uniform(0.1, 0.4))
        
        human_behavior(page, 1, 2)
        
        # 如果有图片需要上传
        if image_paths and len(image_paths) > 0:
            # Twitter最多支持4张图片
            upload_images = image_paths[:4]
            print(f"准备上传 {len(upload_images)} 张图片")
            
            # 验证图片文件是否存在
            valid_images = []
            for img_path in upload_images:
                if os.path.exists(img_path):
                    valid_images.append(img_path)
                    print(f"验证图片存在: {img_path}")
                else:
                    print(f"图片文件不存在: {img_path}")
            
            if not valid_images:
                print("没有有效的图片文件，跳过上传")
            else:
                # 基于HTML分析，正确的图片上传按钮选择器
                upload_button_selectors = [
                    "button[aria-label='Add photos or video']",
                    "div[data-testid='toolBar'] button[aria-label*='photo']",
                    "div[data-testid='toolBar'] button[aria-label*='video']",
                    "nav[role='navigation'] button[aria-label*='photo']",
                    "nav[role='navigation'] button[aria-label*='video']"
                ]
                
                upload_button = None
                for selector in upload_button_selectors:
                    try:
                        temp_button = page.locator(selector).first
                        if temp_button and temp_button.is_visible():
                            upload_button = temp_button
                            print(f"找到上传按钮: {selector}")
                            break
                    except Exception:
                        continue
                
                if not upload_button:
                    # 使用JavaScript直接查找和点击上传按钮
                    try:
                        found = page.evaluate("""() => {
                            // 查找工具栏
                            const toolBar = document.querySelector('[data-testid="toolBar"]');
                            if (!toolBar) {
                                console.log('未找到工具栏');
                                return false;
                            }
                            
                            // 在工具栏中查找上传按钮
                            const buttons = toolBar.querySelectorAll('button');
                            for (const button of buttons) {
                                const ariaLabel = button.getAttribute('aria-label') || '';
                                if (ariaLabel.toLowerCase().includes('photo') || 
                                    ariaLabel.toLowerCase().includes('video')) {
                                    console.log('找到上传按钮:', ariaLabel);
                                    return {found: true, selector: 'JavaScript'};
                                }
                            }
                            
                            // 如果没找到，尝试查找所有可能的上传相关按钮
                            const allButtons = document.querySelectorAll('button');
                            for (const button of allButtons) {
                                const ariaLabel = (button.getAttribute('aria-label') || '').toLowerCase();
                                if (ariaLabel.includes('add') && (ariaLabel.includes('photo') || ariaLabel.includes('video'))) {
                                    console.log('通过通用搜索找到上传按钮:', ariaLabel);
                                    return {found: true, selector: 'JavaScript-generic'};
                                }
                            }
                            
                            return {found: false};
                        }""")
                        
                        if found.get('found'):
                            print(f"通过JavaScript找到上传按钮: {found.get('selector')}")
                        else:
                            print("JavaScript也无法找到上传按钮，跳过图片上传")
                            valid_images = []
                    except Exception as e:
                        print(f"JavaScript查找上传按钮失败: {str(e)}")
                        valid_images = []
                
                # 如果找到了上传按钮且有有效图片，进行上传
                if valid_images and (upload_button or found.get('found')):
                    try:
                        # 设置文件选择器处理
                        def handle_file_chooser(file_chooser):
                            """处理文件选择对话框"""
                            try:
                                print(f"文件选择对话框已打开，准备上传 {len(valid_images)} 个文件")
                                file_chooser.set_files(valid_images)
                                print("文件已设置到选择器")
                            except Exception as e:
                                print(f"设置文件到选择器时出错: {str(e)}")
                        
                        # 监听文件选择器事件
                        page.on("filechooser", handle_file_chooser)
                        
                        # 点击上传按钮
                        if upload_button:
                            upload_button.click()
                            print("成功点击上传按钮")
                        else:
                            # 使用JavaScript点击
                            page.evaluate("""() => {
                                const toolBar = document.querySelector('[data-testid="toolBar"]');
                                if (toolBar) {
                                    const buttons = toolBar.querySelectorAll('button');
                                    for (const button of buttons) {
                                        const ariaLabel = button.getAttribute('aria-label') || '';
                                        if (ariaLabel.toLowerCase().includes('photo') || 
                                            ariaLabel.toLowerCase().includes('video')) {
                                            button.click();
                                            return;
                                        }
                                    }
                                }
                            }""")
                            print("通过JavaScript点击上传按钮")
                        
                        # 等待文件上传完成
                        human_behavior(page, 2, 4, True, False)
                        
                        # 等待图片处理完成
                        try:
                            # 等待图片预览出现或上传完成的指示器
                            page.wait_for_selector("div[data-testid='toolBar'] img, div[aria-label*='Remove'], button[aria-label*='Remove']", timeout=15000)
                            print("图片上传并处理完成")
                        except Exception:
                            print("等待图片处理完成超时，但继续发布")
                        
                        # 移除文件选择器监听器
                        page.remove_listener("filechooser", handle_file_chooser)
                        
                    except Exception as e:
                        print(f"上传图片过程中出错: {str(e)}")
                        # 移除监听器
                        try:
                            page.remove_listener("filechooser", handle_file_chooser)
                        except:
                            pass
        
        # 查找并点击发布按钮
        tweet_button_selectors = [
            "div[data-testid='tweetButton']",
            "button[data-testid='tweetButton']",
            "div[data-testid='tweetButtonInline']",
            "button[data-testid='tweetButtonInline']",
            "div[role='button'][data-testid='tweetButton']",
            "button[aria-label='Tweet']"
        ]
        
        tweet_button = None
        for selector in tweet_button_selectors:
            temp_button = page.locator(selector).first
            if temp_button and temp_button.is_visible():
                # 检查按钮是否可点击（不是禁用状态）
                if not temp_button.is_disabled():
                    tweet_button = temp_button
                    print(f"找到发布按钮: {selector}")
                    break
        
        if not tweet_button:
            print("找不到可用的发布按钮")
            save_error_data(page, "post_tweet", "no_tweet_button")
            return False
        
        # 点击发布按钮
        tweet_button.click()
        print("已点击发布按钮")
        
        # 等待推文发布完成
        human_behavior(page, 3, 5, True, False)
        
        # 处理可能出现的弹窗（如安全验证、功能介绍等）
        try:
            # 常见的弹窗确认按钮选择器
            popup_button_selectors = [
                "button[data-testid='confirmationSheetConfirm']",  # 确认按钮
                "div[data-testid='confirmationSheetConfirm']",     # 确认按钮（div形式）
                "button:has-text('Got it')",                       # "Got it" 按钮
                "button:has-text('Continue')",                     # "Continue" 按钮
                "button:has-text('OK')",                           # "OK" 按钮
                "button:has-text('Confirm')",                      # "Confirm" 按钮
                "button[aria-label*='Continue']",                  # 包含Continue的按钮
                "button[aria-label*='Got it']",                    # 包含Got it的按钮
                "div[role='dialog'] button",                       # 对话框中的按钮
                "div[data-testid='modal'] button"                  # 模态框中的按钮
            ]
            
            # 检查是否有弹窗出现
            popup_found = False
            for selector in popup_button_selectors:
                try:
                    popup_button = page.locator(selector).first
                    if popup_button and popup_button.is_visible():
                        print(f"检测到弹窗，准备点击确认按钮: {selector}")
                        popup_button.click()
                        popup_found = True
                        print("已点击弹窗确认按钮")
                        human_behavior(page, 1, 2, True, False)
                        break
                except Exception:
                    continue
            
            # 如果没有找到标准选择器，尝试使用JavaScript查找和点击
            if not popup_found:
                js_result = page.evaluate("""() => {
                    // 查找包含常见确认文本的按钮
                    const buttons = document.querySelectorAll('button');
                    const confirmTexts = ['got it', 'continue', 'ok', 'confirm', 'close', '知道了', '继续', '确认', '关闭'];
                    
                    for (const button of buttons) {
                        const text = (button.textContent || '').toLowerCase().trim();
                        const ariaLabel = (button.getAttribute('aria-label') || '').toLowerCase();
                        
                        for (const confirmText of confirmTexts) {
                            if (text.includes(confirmText) || ariaLabel.includes(confirmText)) {
                                // 检查按钮是否在可见的模态框或对话框中
                                const rect = button.getBoundingClientRect();
                                if (rect.width > 0 && rect.height > 0) {
                                    console.log('找到弹窗确认按钮:', text || ariaLabel);
                                    button.click();
                                    return {found: true, text: text || ariaLabel};
                                }
                            }
                        }
                    }
                    return {found: false};
                }""")
                
                if js_result.get('found'):
                    popup_found = True
                    print(f"通过JavaScript找到并点击了弹窗按钮: {js_result.get('text')}")
                    human_behavior(page, 1, 2, True, False)
            
            if not popup_found:
                print("未检测到需要处理的弹窗")
                
        except Exception as e:
            print(f"处理弹窗时出错: {str(e)}")
            # 弹窗处理失败不影响主流程，继续执行
        
        # 检查是否发布成功 - 查找成功提示或URL变化
        success = False
        try:
            # 方法1: 检查是否有成功提示
            success_indicators = [
                "div[data-testid='toast']",  # 成功提示toast
                "div[role='alert']",         # 警告/成功消息
            ]
            
            for indicator in success_indicators:
                if page.locator(indicator).is_visible():
                    success = True
                    break
            
            # 方法2: 检查URL是否变化（发布后可能跳转）
            current_url = page.url
            if "status" in current_url or current_url != "https://twitter.com/home":
                success = True
            
            # 方法3: 检查推文输入框是否被清空
            if tweet_box.text_content().strip() == "":
                success = True
                
        except Exception:
            # 如果检查失败，默认认为成功
            success = True
        
        if success:
            print("推文发布成功!")
            return True
        else:
            print("推文可能发布失败")
            save_error_data(page, "post_tweet", "publish_failed")
            return False
            
    except Exception as e:
        print(f"发布推文时出错: {str(e)}")
        save_error_data(page, "post_tweet", f"exception_{str(e).replace(' ', '_')[:30]}")
        return False

def post_multiple_tweets(page, tweets_data, delay_range=None, success_file=None, results_file=None):
    """
    批量发布多条推文
    
    参数:
    - page: Playwright页面对象
    - tweets_data: 推文数据列表，每个元素是字典 {'text': '推文内容', 'images': ['图片路径1', '图片路径2']}
    - delay_range: 推文之间的延迟时间范围（秒），如果为None则使用配置文件中的设置
    - success_file: 成功发布记录文件路径
    - results_file: 实时保存结果的文件路径
    
    返回:
    - dict: 发布结果统计 {'success': 成功数量, 'failed': 失败数量, 'details': 详细结果}
    """
    # 如果没有指定延迟范围，使用配置文件中的设置
    if delay_range is None:
        behavior_config = get_behavior_config()
        delay_range = (behavior_config["TWEET_DELAY_MIN"], behavior_config["TWEET_DELAY_MAX"])
    
    print(f"准备批量发布 {len(tweets_data)} 条推文")
    
    results = {
        'success': 0,
        'failed': 0,
        'details': []
    }
    
    for i, tweet_data in enumerate(tweets_data):
        tweet_text = tweet_data.get('text', '')
        image_paths = tweet_data.get('images', [])
        
        print(f"发布第 {i+1}/{len(tweets_data)} 条推文...")
        
        try:
            success = post_tweet(page, tweet_text, image_paths)
            
            result_detail = {
                'index': i + 1,
                'text': tweet_text,
                'image_count': len(image_paths) if image_paths else 0,
                'success': success,
                'timestamp': time.strftime("%Y-%m-%d %H:%M:%S")
            }
            
            results['details'].append(result_detail)
            
            if success:
                results['success'] += 1
                print(f"第 {i+1} 条推文发布成功")
                
                # 实时保存成功发布的推文记录
                if success_file:
                    published_data = {
                        'text': tweet_text,
                        'images': image_paths if image_paths else [],
                        'timestamp': time.strftime("%Y-%m-%d %H:%M:%S")
                    }
                    append_published_tweet(success_file, published_data)
            else:
                results['failed'] += 1
                print(f"第 {i+1} 条推文发布失败")
            
            # 实时保存发布结果
            if results_file:
                with open(results_file, 'w', encoding='utf-8') as f:
                    json.dump(results, f, ensure_ascii=False, indent=2)
            
            # 如果不是最后一条推文，添加随机延迟
            if i < len(tweets_data) - 1:
                delay_time = random.randint(delay_range[0], delay_range[1])
                print(f"等待 {delay_time} 秒后发布下一条推文...")
                human_behavior(page, delay_time, delay_time + 10, True, True)
                
        except Exception as e:
            print(f"处理第 {i+1} 条推文时出错: {str(e)}")
            results['failed'] += 1
            results['details'].append({
                'index': i + 1,
                'text': tweet_text[:50] + '...' if len(tweet_text) > 50 else tweet_text,
                'image_count': len(image_paths) if image_paths else 0,
                'success': False,
                'error': str(e),
                'timestamp': time.strftime("%Y-%m-%d %H:%M:%S")
            })
            
            # 实时保存发布结果（包括失败的）
            if results_file:
                with open(results_file, 'w', encoding='utf-8') as f:
                    json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"批量发布完成: 成功 {results['success']} 条, 失败 {results['failed']} 条")
    
    # 最终保存发布结果到统一目录
    if results_file:
        print(f"发布结果已实时保存到: {results_file}")
    
    return results

def run_post_tweet_task(playwright: Playwright) -> None:
    """推文发布功能的主函数"""
    print("=== Twitter 推文发布功能 ===")
    
    # 确保所有必要的目录存在
    ensure_directories()
    
    # 从配置文件获取参数
    file_config = get_file_config()
    tweet_content_file = file_config["TWEET_CONTENT_FILE"]  # 推文内容文件
    tweet_progress_file = file_config["TWEET_PROGRESS_FILE"]  # 推文进度记录文件
    
    # 检查必要文件是否存在
    if not os.path.exists(tweet_content_file):
        print(f"❌ 推文内容文件不存在: {tweet_content_file}")
        return
    
    # 加载推文内容
    tweet_contents = load_tweet_content_from_file(tweet_content_file)
    if not tweet_contents:
        print(f"❌ 推文内容列表为空或无法加载文件 {tweet_content_file}")
        return
    
    # 加载已发布的推文记录（断点恢复）
    published_tweets = load_published_tweets(tweet_progress_file)
    
    # 过滤出未发布的推文内容
    unpublished_tweets = filter_unpublished_tweets(tweet_contents, published_tweets)
    
    if not unpublished_tweets:
        print("🎉 所有推文都已发布完成，无需继续发布！")
        return
    
    print(f"📝 本次将发布 {len(unpublished_tweets)} 条未发布的推文")
    
    # 设置浏览器并登录
    browser, context, page = setup_browser_and_login(playwright)
    if not all([browser, context, page]):
        print("❌ 无法设置浏览器或登录，退出程序")
        return
    
    try:
        # 登录成功后，开始批量发布推文
        human_behavior(page, 3, 6, True, True)
        
        print(f"\n📤 开始批量发布 {len(unpublished_tweets)} 条推文...")
        behavior_config = get_behavior_config()
        print(f"⏱️ 推文间隔设置为 {behavior_config['TWEET_DELAY_MIN']}-{behavior_config['TWEET_DELAY_MAX']} 秒")
        print(f"💾 成功发布的推文将实时保存到: {tweet_progress_file}")
        
        # 准备实时保存的结果文件
        from .config import get_directories
        directories = get_directories()
        results_dir = directories["RESULTS_DIR"]
        
        result_filename = os.path.join(results_dir, f"tweet_results_{time.strftime('%Y%m%d_%H%M%S')}.json")
        print(f"📊 发布结果将实时保存到: {result_filename}")
        
        # 使用配置文件中的延迟设置，并传入成功记录文件路径和结果文件路径
        results = post_multiple_tweets(page, unpublished_tweets, success_file=tweet_progress_file, results_file=result_filename)
        
        print(f"\n📊 批量发布结果：")
        print(f"✅ 成功: {results['success']} 条")
        print(f"❌ 失败: {results['failed']} 条")
        
        print(f"\n🎉 推文发布任务完成！")
        
    except Exception as e:
        print(f"❌ 推文发布过程中出现错误: {str(e)}")
        print(f"💡 提示: 已成功发布的推文已保存，发布结果已实时保存，可以重新运行程序继续发布")
    finally:
        # 清理资源
        context.close()
        browser.close()

if __name__ == "__main__":
    with sync_playwright() as playwright:
        run_post_tweet_task(playwright) 