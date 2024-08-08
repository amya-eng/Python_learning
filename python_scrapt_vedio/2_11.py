import aiohttp
import asyncio
from bs4 import BeautifulSoup
from Crypto.Cipher import AES
import binascii
import os
import subprocess
import re
from Crypto.Util.Padding import pad, unpad
import Crypto.Util.Padding
import Crypto
import requests
import aiohttp
import aiofiles


async def get_video_url(url):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers={'User-Agent': 'Mozilla/5.0'}) as response:
                if response.status == 200:
                    html = await response.text()
                    bsObj = BeautifulSoup(html, 'html.parser')
                    tag = bsObj.find('video').find('source')
                    source = tag["src"]
                    return source
    except Exception as e:
        print(f"Error getting video url: {e}")
        return None

def parse_m3u8_text(m3u8_text):
    m3u8_text = m3u8_text.split()
    encode_info = [line for line in m3u8_text if line.startswith('#EXT-X-KEY:')][0]
    pattern = r"#EXT-X-KEY:METHOD=(.*),URI=\"(.*)\",IV=(.*)"
    match = re.search(pattern, encode_info)

    if match:
        key_url = match.group(2)
        IV = match.group(3)[2:]
    else:
        raise Exception('Failed to parse')

    return key_url, IV

async def download_one_seg(key, iv, url, folder, file, video_segments):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                os.makedirs(folder, exist_ok=True)
                file_path = os.path.join(folder, file)
                async with aiofiles.open(file_path, 'wb') as f:
                    await f.write(await response.read())

                cipher = AES.new(key, AES.MODE_CBC, iv)

                async with aiofiles.open(file_path, 'rb') as f:
                    data = await f.read()

                block_size = AES.block_size
                decrypted_data = b''

                for i in range(0, len(data), block_size):
                    block = data[i:i + block_size]
                    decrypted_block = cipher.decrypt(block)
                    decrypted_data += decrypted_block

                decrypted_file_path = os.path.join(folder, 'video_data_decrypted',
                                                   f'decrypted{file.split(".")[0]}.{file.split(".")[1]}')

                os.makedirs(os.path.dirname(decrypted_file_path), exist_ok=True)

                async with aiofiles.open(decrypted_file_path, 'wb') as f:
                    await f.write(data)

                video_segments.append(decrypted_file_path)

async def download_one_page(m3u8_url, folder):
    key_url, IV = parse_m3u8_text(requests.get(m3u8_url).text)
    key_url = m3u8_url.rsplit('/', 1)[0] + '/' + key_url
    key = requests.get(key_url).content
    iv = binascii.unhexlify(IV)
    async with aiohttp.ClientSession() as session:
        response = await session.get(m3u8_url)

    async with aiofiles.open(os.path.join(folder, 'video.m3u8'), 'wb') as file:
        file.write(await response.content.read())

    n = 1
    video_segments = []

    async with aiofiles.open(os.path.join(folder, 'video.m3u8'), 'r') as f:
        video_seg = {}

        for line in f:
            line = line.strip()
            if line.startswith("#"):
                continue
            video_seg[line] = f"{n}.ts"
            n += 1

        tasks = []

        for url, file_name in video_seg.items():
            task = asyncio.create_task(download_one_seg(key, iv, url, os.path.join(folder, 'video_data'), file_name, video_segments))
            tasks.append(task)

        await asyncio.gather(*tasks)

    video_segments = sorted(video_segments, key=lambda x: int(x.split('/')[-1].split('.')[0]))

    async with aiofiles.open(f"{folder}_video.lst", "w") as file:
        for video_segment in video_segments:
            await file.write(f"file '{video_segment}'\n")

    cmd = f"ffmpeg -f concat -i {folder}_video.lst -c copy {folder}_video.ts"
    subprocess.call(cmd, shell=True)

    input_file = f"{folder}_video.ts"
    output_file = f"{folder}_video.mp4"
    command = f"ffmpeg -i {input_file} -c:v copy -c:a aac -strict experimental {output_file}"
    subprocess.call(command, shell=True)

    print(f"Processing done: {folder}")

async def main():
    base_url = "https://www.yitutrend.com/vp-ectid/v3-983203-"
    base_folder = "folder"
    num = 2
    folder_map = {}

    for i in range(1, num + 1):
        m3u8_url = f"{base_url}{i}.html"
        folder = f"{base_folder}{i}"
        folder_map[m3u8_url] = folder
        os.makedirs(folder, exist_ok=True)

    tasks = []

    for url, folder_name in folder_map.items():
        m3u8_url = await get_video_url(url)

        if m3u8_url:
            task = asyncio.create_task(download_one_page(m3u8_url, folder_name))
            tasks.append(task)

    await asyncio.gather(*tasks)
    print("All files downloaded")

if __name__ == "__main__":
    asyncio.run(main())
