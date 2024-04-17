# optimus


# Setup
* install ffmpeg

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