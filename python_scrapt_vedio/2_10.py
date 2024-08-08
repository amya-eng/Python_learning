# 可行
from urllib.request import Request, urlopen
from urllib.error import HTTPError
from bs4 import BeautifulSoup
import requests
import subprocess
import re
from Crypto.Cipher import AES
import binascii

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

    ## 获得加密key.key的url和IV
    match = re.search(pattern, encode_info)
    if match:
        key_url = match.group(2)
        IV = match.group(3)
        IV = IV[2:]                 # 去掉0x前缀
    else:
        raise Exception('解析失败')
    return key_url, IV


def download_one_page(url, i):
    m3u8_url = get_video_url(url)
    if m3u8_url is None:
        return
    else:
        # 本地保存文件路径
        local_filename = "video.m3u8"

        # 发起GET请求获取M3U8文件内容
        response = requests.get(m3u8_url, verify=False)

        # 获取密钥和初始向量
        key_url, IV = parse_m3u8_text(response.text)
        key_url = m3u8_url[:-10] + key_url
        print(key_url)
        # key_url = 'https://hnzy.bfvvs.com/play/yb82pnoe/' + key_url
        key = requests.get(key_url).content
        iv = binascii.unhexlify(IV)  # iv从十六进制转化为字节
        # 将M3U8文件内容保存到本地
        with open(local_filename, 'wb') as file:
            file.write(response.content)

        print("M3U8文件已保存到", local_filename)

        # 输出MP4文件路径
        # output_filename = "output.mp4"
        #
        # cmd = (f"ffmpeg -protocol_whitelist file,http,https,tcp,tls,crypto -i "
        #        f"{local_filename} -c copy -bsf:a aac_adtstoasc {output_filename}")
        # subprocess.call(cmd, shell=True)

        # 解析m3u8文件
        n = 1
        video_segments = []
        with open("video.m3u8", mode="r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()  # 先去掉空格, 空白, 换行符
                if line.startswith("#"):  # 如果以#开头. 我不要
                    continue

                # 下载视频片段
                resp3 = requests.get(line)
                f = open(f"video_data/{n}.ts", mode="wb")
                f.write(resp3.content)
                f.close()
                resp3.close()

                # 解密视频
                # 初始化AES解密器
                cipher = AES.new(key, AES.MODE_CBC, iv)

                # 从文件中读取需要解密的数据
                with open(f'video_data/{n}.ts', 'rb') as f:
                    data = f.read()

                try:
                    decrypted_data = cipher.decrypt(block)
                except:
                    block_size = AES.block_size
                    decrypted_data = b''

                    for i in range(0, len(data), block_size):
                        block = data[i:i + block_size]
                        decrypted_block = cipher.decrypt(block)
                        decrypted_data += decrypted_block

                with open(f'video_data_decrypted/{n}.ts', 'wb') as f:
                    f.write(decrypted_data)

                video_segments.append(f'video_data_decrypted/{n}.ts')
                print(f"seg{n} is done.")
                n += 1

    # 排序视频片段
    video_segments = sorted(video_segments, key=lambda x: int(x.split('/')[-1].split('.')[0]))

    # 合并视频片段为一个视频文件
    with open("video.lst", "w") as file:
        for video_segment in video_segments:
            file.write(f"file '{video_segment}'\n")

    cmd = f"ffmpeg -f concat -i video.lst -c copy video.ts"
    subprocess.call(cmd, shell=True)

    # 转换视频格式为mp4
    input_file = "video.ts"
    output_file = f"video{i}.mp4"
    command = f"ffmpeg -i {input_file} -c:v copy -c:a aac -strict experimental {output_file}"
    subprocess.call(command, shell=True)

    print(f"video{i} is done.")

def main():
    base_url = "https://www.yitutrend.com/vp-ectid/v3-983203-"
    num = 47             # 集数
    for i in range(2, num + 1):
        url = f"{base_url}{i}.html"
        download_one_page(url, i)
    print('done.')

if __name__ == "__main__":
    main()
