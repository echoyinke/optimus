import asyncio
from twikit import Client

USERNAME = "mysticwhis45664"
# EMAIL = 'weirdoyinke@gmail.com'
PASSWORD = "YinKe@123"
# 要挂代理，否则会出现`httpx.ConnectTimeout` 的问题
PROXY = "http://127.0.0.1:4780"


# 初始化客户端
client = Client('en-US', proxy=PROXY)

async def search_tweets_by_keywords(client, keywords, **kwargs):
    # 按照关键词搜索推文
    tweets = await client.search_tweet(keywords, 'Latest', **kwargs)

    tweet_id_list = []
    # 打印搜索结果
    for tweet in tweets:
        print(tweet.id, tweet.text)
        tweet_id_list.append(tweet.id)
    
    # 返回推文ID列表
    return tweet_id_list

async def search_tweets_by_username(client, username, **kwargs):
    # 搜索特定用户的推文，可以指定count
    user = await client.get_user_by_screen_name(username)
    user_id = user.id
    tweets = await client.get_user_tweets(user_id, 'Tweets', **kwargs)

    tweet_id_list = []
    # 打印搜索结果
    for tweet in tweets:
        print(tweet.id, tweet.text)
        tweet_id_list.append(tweet.id)
    
    # 返回推文ID列表
    return tweet_id_list
    

async def main():
    await client.login(
        auth_info_1=USERNAME,
        # auth_info_2=EMAIL,
        password=PASSWORD
    )

    media_ids = [
        # await client.upload_media('/Users/zzy/Documents/AI图片素材/小柯基.jpeg'),
        await client.upload_media('/Users/yinke/VscodeProject/optimus/outputs/crawl_pics/art4fap/art4fap-468473-Yelena__Commission_1.png')
    ]

    # 搜索推文（这里可以扩展，比如搜索top的用户列表，汇聚到一个list中，后续可以随机抽取）
    tweet_id_list = await search_tweets_by_username(client, USERNAME)
    print(tweet_id_list)
    for tweet_id in tweet_id_list:
        # 回复推文
        await client.create_tweet(
            text='GOOD!',
            media_ids=media_ids,
            reply_to=tweet_id,
        )

if __name__ == '__main__':
    asyncio.run(main())

