'''
After you've set your subscription key, run this application from your working
directory with this command: python TTSSample.py
'''
import os
import requests
import time
from xml.etree import ElementTree



'''
If you prefer, you can hardcode your subscription key as a string and remove
the provided conditional statement. However, we do recommend using environment
variables to secure your subscription keys. The environment variable is
set to SPEECH_SERVICE_KEY in our sample.

For example:
subscription_key = "Your-Key-Goes-Here"
'''

if 'SPEECH_SERVICE_KEY' in os.environ:
    subscription_key = os.environ['SPEECH_SERVICE_KEY']
else:
    subscription_key = "dc00d3aa5b204db4a4ffbba9b96560d3"
    # print('Environment variable for your subscription key is not set.')
    # exit()

class AzureTextToSpeech:
    def __init__(self, subscription_key, region='eastasia'):
        self.subscription_key = subscription_key
        self.region = region
        self.timestr = time.strftime("%Y%m%d-%H%M")
        self.access_token = None
        self.get_token()


    '''
    The TTS endpoint requires an access token. This method exchanges your
    subscription key for an access token that is valid for ten minutes.
    '''
    def get_token(self):
        fetch_token_url = f"https://{self.region}.api.cognitive.microsoft.com/sts/v1.0/issuetoken"
        headers = {
            'Ocp-Apim-Subscription-Key': self.subscription_key
        }
        response = requests.post(fetch_token_url, headers=headers)
        self.access_token = str(response.text)

    def tts(self, text, output_wav_file_path, ShortName='zh-CN-YunxiNeural'):
        base_url = f'https://{self.region}.tts.speech.microsoft.com/'
        path = 'cognitiveservices/v1'
        constructed_url = base_url + path
        headers = {
            'Authorization': 'Bearer ' + self.access_token,
            'Content-Type': 'application/ssml+xml',
            'X-Microsoft-OutputFormat': 'riff-24khz-16bit-mono-pcm',
            'User-Agent': 'YOUR_RESOURCE_NAME'
        }
        xml_body = ElementTree.Element('speak', version='1.0')
        xml_body.set('{http://www.w3.org/XML/1998/namespace}lang', 'zh-CN')
        voice = ElementTree.SubElement(xml_body, 'voice')
        voice.set('{http://www.w3.org/XML/1998/namespace}lang', 'zh-CN')
        # zh-CN-YunyeNeural、zh-CN-YunxiNeural 是使用什么声音输出，可以看代码最后一行app.get_voices_list()获取节点支持的语音输出类型，填ShortName
        # voice.set('name', 'zh-CN-YunyeNeural') # Short name for 'Microsoft Server Speech Text to Speech Voice (en-US, Guy24KRUS)'
        voice.set('name', ShortName) # Short name for 'Microsoft Server Speech Text to Speech Voice (en-US, Guy24KRUS)'
        voice.text = text
        body = ElementTree.tostring(xml_body)

        response = requests.post(constructed_url, headers=headers, data=body)
        '''
        If a success response is returned, then the binary audio is written
        to file in your working directory. It is prefaced by sample and
        includes the date.
        '''
        if response.status_code == 200:
            with open(output_wav_file_path, 'wb') as audio:
                audio.write(response.content)
                # print("\nStatus code: " + str(response.status_code) + "\nYour TTS is ready for playback.\n")
        else:
            print("\nStatus code: " + str(response.status_code) + "\nSomething went wrong. Check your subscription key and headers.\n")
            print("Reason: " + str(response.reason) + "\n")

    def get_voices_list(self):
        base_url = f'https://{self.region}.tts.speech.microsoft.com/'
        path = 'cognitiveservices/voices/list'
        constructed_url = base_url + path
        headers = {
            'Authorization': 'Bearer ' + self.access_token,
        }
        response = requests.get(constructed_url, headers=headers)
        if response.status_code == 200:
            print("\nAvailable voices: \n" + response.text)
        else:
            print("\nStatus code: " + str(response.status_code) + "\nSomething went wrong. Check your subscription key and headers.\n")

if __name__ == "__main__":
    app = AzureTextToSpeech(subscription_key)
    text = "问出这个问题的，是宁无邪。宁无邪很平静，关于第二点，为何有人没有中毒，他已经猜到原因，只是在看到自己的得力下属任随云站起来的时候，他也忍不住自嘲苦笑。“我想知道，你先前所表现的种种，都展现出了你作为沈将军儿子的睿智和态度，如今，江湖帝国本可以和解，你现在的举动，会将这一切毁于一旦你可知道？”言醒面对宁无邪的问题，嘲讽道：“如今荒郊野外，只剩下你们三百人，只要你们死了，又有谁会知道今日所发生的？”“至于你问我为什么，呵，如果是沈小猎的话，他的的确确，会促成江湖与帝国的和解。可我啊，不是沈小猎。”满场皆惊。“若非沈将军的儿子……怎么可能……”说话的是玄生十二，玄生十二如同宁无邪一般，也没有想到自己的大护法徐浮会背叛自己。"
    # text = "你好啊"
    app.tts(text, "output2.wav")
    # Get a list of voices https://docs.microsoft.com/en-us/azure/cognitive-services/speech-service/rest-text-to-speech#get-a-list-of-voices
    # 查看节点支持的语言类型
    # app.get_voices_list()