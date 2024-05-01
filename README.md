# optimus
[ ] 文本分割


# Setup
* install [ffmpeg](https://ffmpeg.org/download.html)
  * for [linux](https://json2video.com/how-to/ffmpeg-course/install-ffmpeg-linux.html)
  * for [windows](https://blog.csdn.net/csdn_yudong/article/details/129182648)
* install [torch](https://pytorch.org/get-started/locally/)

## GPT_SoVITS
使用不同的tts模型：
只需更改：
`GPT_SoVITS_main/gweight.txt`和`GPT_SoVITS_main/sweight.txt`

如真白花音的模型：
gweight.txt：
GPT_SoVITS/pretrained_models/BAICAI-JA-e10.ckpt

sweight.txt：
GPT_SoVITS/pretrained_models/BAICAI-JA_e70_s11410.pth


如果想用重新使用默认模型的话，请将gweight.txt和sweight.txt删除