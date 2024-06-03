import base64
import os
import requests

engine_id = "stable-diffusion-xl-1024-v1-0"
api_host = os.getenv('API_HOST', 'https://api.stability.ai')
api_key = 'sk-UZC78xrYawf2cW6l8UwgHIx5S8QRmORkMeb2DCbcVhzEB0Ih'

if api_key is None:
    raise Exception("Missing Stability API key.")

def text_to_image_by_sd(text_prompts, output_image_path):
    # output_image_path = "xxx.png"
    response = requests.post(
        f"{api_host}/v1/generation/{engine_id}/text-to-image",
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Bearer {api_key}"
        },
        json={
            "text_prompts": text_prompts,
            "cfg_scale": 7,
            "height": 1024,
            "width": 1024,
            "samples": 1,
            "steps": 30,
            # "sampler": "DDIM", "DDPM" ...
        },
    )

    if response.status_code != 200:
        raise Exception("Non-200 response: " + str(response.text))

    data = response.json()

    for i, image in enumerate(data["artifacts"]):
        with open(output_image_path, "wb") as f:
            f.write(base64.b64decode(image["base64"]))

if __name__ == "__main__":
    text_prompts = [
        {
            "text": "((best quality), (((ultradetailed))), (((masterpiece))), illustration,  old tungsten light bulb, black wire, hanging centrally, flickering dim light, serene atmosphere, ink drop in water, spreading in room, large round table, worn and faded, small ornate table clock, intricate patterns, ticking sound, ten people, various clothing, slightly tattered, faces covered in dust, some resting on table, some leaning back in chairs, all deeply asleep",
            # "weight": 0.5
        }
    ]
    output_image_path = "output.png"
    text_to_image_by_sd(text_prompts, output_image_path)
