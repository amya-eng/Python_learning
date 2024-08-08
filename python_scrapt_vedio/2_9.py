from urllib.request import Request, urlopen
from urllib.error import HTTPError
from bs4 import BeautifulSoup
import requests
from Crypto.Cipher import AES
import binascii
import os
import threading
import subprocess
import re
from Crypto.Util.Padding import pad, unpad
import Crypto.Util.Padding
import Crypto

def get_video_url(url):
    try:
        req = Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        html = urlopen(req)
    except HTTPError:
        return None
    try:
        bsObj = BeautifulSoup(html.read(), 'html.parser')
        tag = bsObj.find('video').find('source')
        source = tag["src"]
    except (AttributeError, KeyError) as e:
        return None
    return source

def parse_m3u8_text(m3u8_text):
    m3u8_text = m3u8_text.split()
    encode_info = [line for line in m3u8_text if line.startswith('#EXT-X-KEY:')][0]
    pattern = r"#EXT-X-KEY:METHOD=(.*),URI=\"(.*)\",IV=(.*)"
    match = re.search(pattern, encode_info)

    if match:
        key_url = match.group(2)
        IV = match.group(3)[2:]
    else:
        raise Exception('解析失败')
    return key_url, IV

def download_one_seg(key, iv, url, flod, file, video_segments, lock):
    resp = requests.get(url)
    os.makedirs(flod, exist_ok=True)

    with open(os.path.join(flod, file), 'wb') as f:
        f.write(resp.content)

    cipher = AES.new(key, AES.MODE_CBC, iv)

    with open(os.path.join(flod, file), 'rb') as f:
        data = f.read()

    block_size = AES.block_size
    decrypted_data = b''

    for i in range(0, len(data), block_size):
        block = data[i: i + block_size]
        decrypted_block = cipher.decrypt(block)
        decrypted_data += decrypted_block

    decrypted_file_path = os.path.join(flod, 'video_data_decrypted',
                                       'decrypted' + file.split('.')[0] + '.' + file.split('.')[1])

    os.makedirs(os.path.dirname(decrypted_file_path), exist_ok=True)

    with open(decrypted_file_path, 'wb') as f:
        f.write(data)

    with lock:
        video_segments.append(decrypted_file_path)

def download_one_page(m3u8_url, flod, lock):
    key_url, IV = parse_m3u8_text(requests.get(m3u8_url).text)
    key_url = m3u8_url.rsplit('/', 1)[0] + '/' + key_url
    key = requests.get(key_url).content
    iv = binascii.unhexlify(IV)
    response = requests.get(m3u8_url, verify=False)

    with open(os.path.join(flod, 'video.m3u8'), 'wb') as file:
        file.write(response.content)

    n = 1
    video_segments = []

    with open(os.path.join(flod, 'video.m3u8'), 'r') as f:
        video_seg = {}

        for line in f:
            line = line.strip()
            if line.startswith("#"):
                continue
            video_seg[line] = f"{n}.ts"
            n += 1

        threads = []

        for url, file_name in video_seg.items():
            thread = threading.Thread(target=download_one_seg, args=(key, iv, url, os.path.join(flod, 'video_data'), file_name, video_segments, lock))
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

    video_segments = sorted(video_segments, key=lambda x: int(x.split('/')[-1].split('.')[0]))

    with open(f"{flod}_video.lst", "w") as file:
        for video_segment in video_segments:
            file.write(f"file '{video_segment}'\n")

    cmd = f"ffmpeg -f concat -i {flod}_video.lst -c copy {flod}_video.ts"
    subprocess.call(cmd, shell=True)

    input_file = f"{flod}_video.ts"
    output_file = f"{flod}_video.mp4"
    command = f"ffmpeg -i {input_file} -c:v copy -c:a aac -strict experimental {output_file}"
    subprocess.call(command, shell=True)

    print(f"处理完成: {flod}")

def main():
    base_url = "https://www.yitutrend.com/vp-ectid/v3-983203-"
    base_folder = "folder"
    num = 2
    flod_map = {}

    for i in range(1, num + 1):
        m3u8_url = f"{base_url}{i}.html"
        folder = f"{base_folder}{i}"
        flod_map[m3u8_url] = folder
        os.makedirs(folder, exist_ok=True)

    threads = []
    lock = threading.Lock()

    for url, folder_name in flod_map.items():
        m3u8_url = get_video_url(url)

        if m3u8_url:
            thread = threading.Thread(target=download_one_page, args=(m3u8_url, folder_name, lock))
            threads.append(thread)
            thread.start()

    for thread in threads:
        thread.join()

    print("所有文件下载完成")

if __name__ == "__main__":
    main()
