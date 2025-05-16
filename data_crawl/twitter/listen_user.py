import asyncio
from typing import NoReturn

from twikit import Client, Tweet
from twikit.guest import GuestClient


AUTH_INFO_1 = 'MisticWhisper'
AUTH_INFO_2 = ''
PASSWORD = 'YinKe@123'
PROXY = "http://127.0.0.1:4780"

client = GuestClient('en-US', proxy=PROXY)

# client = Client('en-US', proxy=PROXY)

USER_ID = '44196397' # elonmsk
CHECK_INTERVAL = 60 * 5


def callback(tweet: Tweet) -> None:
    print(f'New tweet posted : {tweet.text}')


async def get_latest_tweet(user_id, tweet_type) -> Tweet:
    return (await client.get_user_tweets(user_id, tweet_type))[0]


async def main() -> NoReturn:
    # await client.login(
    #     auth_info_1=AUTH_INFO_1,
    #     auth_info_2="EMAIL",
    #     password=PASSWORD
    # )

    # # Get user tweets
    await client.activate()

    # user = await client.get_user_by_screen_name("elonmusk")
    # user_id = user.id
    # print(user_id)
    # user_tweets = await user.get_tweets('Tweets')
    # for tweet in user_tweets:
    #     print(tweet)
    # # Get more tweets
    # more_user_tweets = await user_tweets.next()

    before_tweet = await get_latest_tweet(USER_ID, "Tweets")

    while True:
        await asyncio.sleep(CHECK_INTERVAL)
        latest_tweet = await get_latest_tweet(USER_ID, "Tweets")
        if (
            before_tweet != latest_tweet and
            before_tweet.created_at_datetime < latest_tweet.created_at_datetime
        ):
            callable(latest_tweet)
        before_tweet = latest_tweet

asyncio.run(main())