#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Twitter 自动化脚本主入口
支持评论和发布推文功能
"""

from playwright.sync_api import sync_playwright
from twitter_comment import run_comment_task
from twitter_post import run_post_tweet_task
from twitter_common import ensure_directories

def main():
    """主函数，提供功能选择菜单"""
    # 确保所有必要的目录存在
    ensure_directories()
    
    print("=" * 50)
    print("🐦 Twitter 自动化脚本")
    print("=" * 50)
    print("请选择要执行的功能：")
    print("1. 📝 评论功能 - 对指定用户的推文进行评论")
    print("2. 📤 发布功能 - 发布推文（支持文本和图片）")
    print("3. ❌ 退出程序")
    print("=" * 50)
    
    while True:
        try:
            choice = input("请输入选项 (1/2/3): ").strip()
            
            if choice == "1":
                print("\n🎯 启动评论功能...")
                with sync_playwright() as playwright:
                    run_comment_task(playwright)
                break
                
            elif choice == "2":
                print("\n🎯 启动发布功能...")
                with sync_playwright() as playwright:
                    run_post_tweet_task(playwright)
                break
                
            elif choice == "3":
                print("\n👋 程序已退出，再见！")
                break
                
            else:
                print("❌ 无效选择，请输入 1、2 或 3")
                
        except KeyboardInterrupt:
            print("\n\n👋 程序被用户中断，再见！")
            break
        except Exception as e:
            print(f"\n❌ 程序执行出错: {str(e)}")
            break

if __name__ == "__main__":
    main() 