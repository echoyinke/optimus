import requests
from bs4 import BeautifulSoup
import os, json, time

# 全局配置
BASE_URL = "https://www.hentai-foundry.com"
OUTPUT_DIR = "./HentaiFoundry"  # 输出保存目录
# 构造请求会话，附加Headers模拟浏览器
session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/110.0.0.0 Safari/537.36",
    "Accept-Language": "en-US,en;q=0.9",
})

def bypass_age_check():
    """通过年龄验证，获取必要的cookie。"""
    url = f"{BASE_URL}/?enterAgree=1"
    try:
        res = session.get(url)
        # 检查是否成功进入
        if res.status_code == 200:
            print("Age check passed, session cookies:", session.cookies.get_dict())
        else:
            print("Failed to bypass age check, status:", res.status_code)
    except Exception as e:
        print("Error in age check:", e)

def get_soup(url):
    """请求URL并返回解析后的BeautifulSoup对象。若请求失败返回None。"""
    try:
        res = session.get(url)
        if res.status_code != 200:
            print(f"Warning: Received status {res.status_code} for URL: {url}")
            return None
        # 解析 HTML 文档
        html = res.text
        return BeautifulSoup(html, "html.parser")
    except Exception as e:
        print(f"Request error for {url}: {e}")
        return None

def parse_image_page(page_url):
    """解析单个作品页面，返回图片信息字典，包括图片直链和元数据。"""
    soup = get_soup(page_url)
    if not soup:
        return None
    data = {}
    # 标题
    title_tag = soup.find("h1")
    if title_tag:
        data["title"] = title_tag.get_text(strip=True)
    else:
        # 或者通过breadcrumb最后一项获取标题
        crumb = soup.find("div", {"id": "pageTitle"})
        data["title"] = crumb.get_text(strip=True) if crumb else "Unknown"
    # 作者
    author_link = soup.find("a", href=lambda x: x and x.startswith("/user/"))
    if author_link:
        data["author"] = author_link.get_text(strip=True)
    else:
        data["author"] = None
    # 描述
    desc_div = soup.find("div", {"class": "picDescript"})
    if desc_div:
        # 获取纯文本描述（保留换行）
        data["description"] = desc_div.get_text("\n", strip=True)
    else:
        data["description"] = ""
    # 分类
    cat_span = soup.find("span", string="Category")
    if cat_span:
        # 类别可能在 cat_span 的父级或兄弟节点
        parent = cat_span.find_parent()
        if parent and "Category" in parent.get_text():
            cat_info = parent
        # 直接从页面文本提取Category一行:
        cat_line = cat_span.find_parent().get_text(" ", strip=True) if cat_span.find_parent() else ""
        # e.g. "Category Original » Pin-ups"
        data["category"] = cat_line.split("Category")[-1].strip() if cat_line else None
    # 提交日期、浏览次数等元数据：
    info_section = soup.find("h2", string="General Info")
    if info_section:
        info_table = info_section.find_next("table")  # 假设通用信息在table或div中
        if info_table:
            text = info_table.get_text(" ", strip=True)
            # 简单解析关键字段:
            # Date Submitted ..., Views ..., Favorites ..., Rating/Vote Score ...
            if "Date Submitted" in text:
                try:
                    date_sub = text.split("Date Submitted")[1].split("Date")[0]
                except:
                    date_sub = text.split("Date Submitted")[1]
                data["date_submitted"] = date_sub.strip(": ")
            if "Views" in text:
                try:
                    views = text.split("Views")[1].split()[0]
                    data["views"] = int(views.replace(",", ""))
                except:
                    pass
            if "Favorites" in text:
                try:
                    favs = text.split("Favorites")[1].split()[0]
                    data["favorites"] = int(favs.replace(",", ""))
                except:
                    pass
            if "Rating" in text or "Vote Score" in text:
                # 站点用 Vote Score 表示评分值
                try:
                    score = text.split("Score")[1].split()[0]
                    data["score"] = float(score)
                except:
                    pass
    # 标签
    tags_section = soup.find("h2", string="Tags")
    if tags_section:
        tag_links = tags_section.find_next_all("a")
        data["tags"] = [a.get_text(strip=True) for a in tag_links]
    else:
        data["tags"] = []
    # 查找作品显示的图片 <img> 标签；通常原图<img>带有作品标题作为alt
    # 图片直链
    img_tag = soup.find("img", alt=lambda x: x and data.get("title", "") in x)
    if not img_tag:
        container = soup.find("div", {"class": "picContainer"})
        if container:
            img_tag = container.find("img")

    if img_tag:
        img_url = img_tag.get("src")
        
        # 修正 URL 处理
        if img_url.startswith("//"):
            img_url = "https:" + img_url  # 处理协议相对路径
        elif img_url.startswith("/"):
            # 处理相对路径（确保只加正确的域名）
            if "pictures.hentai-foundry.com" in img_url:
                img_url = "https:" + img_url  # 直接补全协议
            else:
                img_url = "https://pictures.hentai-foundry.com" + img_url  # 确保图片域名正确
        
        data["image_url"] = img_url
    else:
        data["image_url"] = None
    return data

def download_image(img_url, save_path):
    """下载图片并保存到指定路径。"""
    try:
        # 为防止某些站点要求Referer，这里加上:
        headers = {"Referer": BASE_URL}
        res = session.get(img_url, headers=headers)
        if res.status_code == 200:
            with open(save_path, "wb") as f:
                f.write(res.content)
            return True
        else:
            print(f"Failed to download image, status {res.status_code}: {img_url}")
    except Exception as e:
        print(f"Error downloading image {img_url}: {e}")
    return False

def crawl_user_gallery(username):
    """爬取指定用户的所有图片和元数据（逐行存储 JSONL，节省内存）。"""
    print(f"Start crawling user: {username}")

    user_dir = os.path.join(OUTPUT_DIR, f"user_{username}")
    os.makedirs(user_dir, exist_ok=True)
    
    meta_file = os.path.join(user_dir, f"{username}_metadata.jsonl")  # 改成 JSONL 格式
    page = 1

    with open(meta_file, "a", encoding="utf-8") as f:  # 追加模式
        while True:
            gallery_url = f"{BASE_URL}/pictures/user/{username}/page/{page}"
            soup = get_soup(gallery_url)
            if not soup:
                break

            # 获取作品页面的链接
            pic_links = soup.select(f"a[href*='/pictures/user/{username}/']")
            pic_page_urls = set(
                BASE_URL + a.get("href") if a.get("href").startswith("/") else a.get("href")
                for a in pic_links if a.get("href") and not a.get("href").strip().endswith(username)
            )
            if not pic_page_urls:
                break

            # 遍历当前页的作品
            for url in pic_page_urls:
                print(f"  Parsing image page: {url}")
                info = parse_image_page(url)
                if not info:
                    continue

                # 下载图片
                img_url = info.get("image_url")
                if img_url:
                    filename = os.path.basename(img_url)
                    save_path = os.path.join(user_dir, filename)
                    if download_image(img_url, save_path):
                        info["saved_path"] = save_path
                        print(f"    Downloaded image: {filename}")

                # **每次存储 JSON 行，避免占用过多内存**
                f.write(json.dumps(info, ensure_ascii=False) + "\n")
                f.flush()  # 立即写入磁盘，避免数据丢失
                
                time.sleep(1)  # 控制爬取速率

            # 检查是否有下一页
            next_link = soup.find("a", string="Next >")
            if next_link:
                page += 1
                continue
            else:
                if len(pic_page_urls) < 25:
                    break
                page += 1

    print(f"Completed user {username}. Metadata saved to {meta_file}.")

def crawl_category(category_id, category_name=None):
    """爬取指定分类ID下的所有图片，逐步存储 JSONL，避免占用过多内存"""
    cat_label = category_name if category_name else str(category_id)
    print(f"Start crawling category: {cat_label} (ID={category_id})")

    cat_dir = os.path.join(OUTPUT_DIR, f"category_{cat_label.replace('/', '_')}")
    os.makedirs(cat_dir, exist_ok=True)

    meta_file = os.path.join(cat_dir, f"{cat_label}_metadata.jsonl")  # 改为 JSONL 格式
    page = 1

    with open(meta_file, "a", encoding="utf-8") as f:  # 追加模式
        while True:
            cat_url = f"{BASE_URL}/categories/{category_id}/{cat_label.replace(' ', '-')}/pictures/page/{page}"
            soup = get_soup(cat_url)
            if not soup:
                break

            # 获取当前页的作品链接
            pic_links = soup.select("a[href*='/pictures/user/']")
            pic_page_urls = set(BASE_URL + a.get("href") for a in pic_links if a.get("href"))

            if not pic_page_urls:
                break

            # 遍历当前页作品
            for url in pic_page_urls:
                print(f"  Parsing image page: {url}")
                info = parse_image_page(url)
                if not info:
                    continue

                # 下载图片
                img_url = info.get("image_url")
                if img_url:
                    filename = os.path.basename(img_url)
                    save_path = os.path.join(cat_dir, filename)
                    if download_image(img_url, save_path):
                        info["saved_path"] = save_path
                        print(f"    Downloaded image: {filename}")

                # **每次存储 JSON 行，避免占用过多内存**
                f.write(json.dumps(info, ensure_ascii=False) + "\n")
                f.flush()  # 立即写入磁盘
                
                time.sleep(1)  # 控制爬取速率

            # 检查是否有下一页
            next_link = soup.find("a", string="Next >")
            if next_link:
                page += 1
                continue
            else:
                if len(pic_page_urls) < 25:
                    break
                page += 1

    print(f"Completed category {cat_label}. Metadata saved to {meta_file}.")

# =============== 主程序调用 =================
if __name__ == "__main__":
    # 示例：爬取用户"GloomFlower"和分类"Original/Pin-ups"
    bypass_age_check()  # 先通过年龄验证获取cookie
    # 爬取指定用户
    crawl_user_gallery("GloomFlower")
    # 爬取指定分类（已知 Original/Pin-ups 的ID是147）
    crawl_category(147, "Original-Pin-ups")