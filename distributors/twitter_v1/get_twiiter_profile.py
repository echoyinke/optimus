from data_crawl.core.utils import *
import logging
import httpx
import twikit.errors as twikit_error
# 设置全局日志配置
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logging.getLogger("httpx").setLevel(logging.WARNING)
# 主脚本 logger
logger = logging.getLogger(__name__)

import asyncio
import requests

from twikit.guest import GuestClient
PROXY = "http://127.0.0.1:4780"

client = GuestClient(proxy=PROXY)


async def main():
    all_user_info=read_data("/Users/yinke/VscodeProject/optimus/outputs/crawl_users/user_info")
    # 读取已处理过的用户名集合
    processed_usernames = set()
    output_path = "/Users/yinke/VscodeProject/optimus/outputs/crawl_users/user_twitter/user_x_info.jsonl"
    if os.path.exists(output_path):
        with open(output_path, "r", encoding="utf-8") as f:
            for line in f:
                try:
                    existing = json.loads(line.strip())
                    processed_usernames.add(existing["screen_name"])
                except Exception:
                    continue
    # Activate the client by generating a guest token.
    await client.activate()
    with jsonlines.open("/Users/yinke/VscodeProject/optimus/outputs/crawl_users/user_twitter/user_x_info.jsonl", mode='a') as writer:

        for info in all_user_info:
            social_links=info['social_links']
            # Get user by screen name
            # 找出twitter url 并分割出 screen name
            twitter_url = next((link for link in social_links if "twitter.com" in link), None)
            if twitter_url:
                screen_name = twitter_url.strip("/").split("/")[-1]
                if screen_name in processed_usernames:
                    logger.info(f"Skipping {screen_name}, already processed.")
                    continue
                logger.info(f"Processing screen name: {screen_name}")
                try:
                    user = await client.get_user_by_screen_name(screen_name)
                except KeyError as e:
                    continue
                except httpx.ConnectTimeout as e:
                    logger.error(f"Sleep {60},cause : {e}")
                    await asyncio.sleep(60)
                    await client.activate()                    
                    continue
                    
                except twikit_error.NotFound as e:
                    logger.error(f"Sleep {60},cause : {e}")
                    await asyncio.sleep(60)
                    await client.activate()                    
                    continue
                    

                except twikit_error.TooManyRequests as e:
                    logger.error(f"Sleep {60},cause : {e}")
                    await asyncio.sleep(60)
                    continue
                    
                
                user_data = {
                    "id": user.id,
                    "created_at": user.created_at,
                    "name": user.name,
                    "screen_name": user.screen_name,
                    "profile_image_url": user.profile_image_url,
                    "profile_banner_url": user.profile_banner_url,
                    "url": user.url,
                    "location": user.location,
                    "description": user.description,
                    "description_urls": user.description_urls,
                    "pinned_tweet_ids": user.pinned_tweet_ids,
                    "is_blue_verified": user.is_blue_verified,
                    "verified": user.verified,
                    "possibly_sensitive": user.possibly_sensitive,
                    "default_profile": user.default_profile,
                    "default_profile_image": user.default_profile_image,
                    "has_custom_timelines": user.has_custom_timelines,
                    "followers_count": user.followers_count,
                    "fast_followers_count": user.fast_followers_count,
                    "normal_followers_count": user.normal_followers_count,
                    "following_count": user.following_count,
                    "favourites_count": user.favourites_count,
                    "listed_count": user.listed_count,
                    "media_count": user.media_count,
                    "statuses_count": user.statuses_count,
                    "is_translator": user.is_translator,
                    "translator_type": user.translator_type,
                    "withheld_in_countries": user.withheld_in_countries,
                }
                writer.write(user_data)
                await asyncio.sleep(5)
                
                banner_url = user.profile_banner_url
                # if banner_url:
                #     try:
                #         response = requests.get(banner_url)
                #         if response.status_code == 200:
                #             with open(f"/Users/yinke/VscodeProject/optimus/outputs/crawl_users/user_twitter/imgs/{screen_name}_banner.jpg", "wb") as f:
                #                 f.write(response.content)
                #             logger.info(f"Downloaded banner for {screen_name}")
                #         else:
                #             logger.warning(f"Failed to download banner for {screen_name}, status code: {response.status_code}")
                #     except Exception as download_err:
                #         logger.warning(f"Error downloading banner for {screen_name}: {download_err}")

                # profile_image_url = user.profile_image_url
                # if profile_image_url:
                #     try:
                #         response = requests.get(profile_image_url)
                #         if response.status_code == 200:
                #             with open(f"/Users/yinke/VscodeProject/optimus/outputs/crawl_users/user_twitter/imgs/{screen_name}_img.jpg", "wb") as f:
                #                 f.write(response.content)
                #             logger.info(f"Downloaded avatar for {screen_name}")
                #         else:
                #             logger.warning(f"Failed to download avatar for {screen_name}, status code: {response.status_code}")
                #     except Exception as download_err:
                #         logger.warning(f"Error downloading avatar for {screen_name}: {download_err}")
        
    logger.info("🎉 All users processed. Program exiting normally.")
asyncio.run(main())
