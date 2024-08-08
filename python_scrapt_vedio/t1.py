# import aiohttp
# import asyncio
# import aiofiles
# from Crypto.Cipher import AES
# import binascii
# import re
# from bs4 import BeautifulSoup
#
#
# async def get_video_url(url):
#     async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False)) as session:
#         async with session.get(url, headers={'User-Agent': 'Mozilla/5.0'}) as response:
#             if response.status != 200:
#                 return None
#             html = await response.text()
#             bsObj = BeautifulSoup(html, 'html.parser')
#             tag = bsObj.find('video').find('source')
#             return tag["src"]
#
#
# async def parse_m3u8_text(m3u8_text):
#     m3u8_text = m3u8_text.split()
#     encode_info = [line for line in m3u8_text if line.startswith('#EXT-X-KEY:')][0]
#
#     pattern = r"#EXT-X-KEY:METHOD=(.*),URI=\"(.*)\",IV=(.*)"
#     match = re.search(pattern, encode_info)
#     if match:
#         key_url = match.group(2)
#         IV = match.group(3)[2:]
#     else:
#         raise Exception('解析失败')
#
#     return key_url, IV
#

# async def download_video_segment(key, iv, encrypted_data, n):
#     cipher = AES.new(key, AES.MODE_CBC, iv)
#     decrypted_data = cipher.decrypt(encrypted_data)
#
#     async with aiofiles.open(f'video_data_decrypted/{n}.ts', 'wb') as f:
#         await f.write(decrypted_data)
#     print(f"seg{n} is done.")
#
#
# async def download_one_page(url, i):
#     m3u8_url = await get_video_url(url)
#     if m3u8_url is None:
#         return
#
#     async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False)) as session:
#         # print(m3u8_url)
#         async with session.get(m3u8_url, verify_ssl=False) as response:
#             if response.status == 200:
#                 m3u8_text = await response.text()
#                 key_url, IV = await parse_m3u8_text(m3u8_text)
#                 key_url = m3u8_url[:-10] + key_url
#                 key_response = await session.get(key_url)
#                 key = await key_response.read()
#                 iv = binascii.unhexlify(IV)
#
#                 async with aiofiles.open("video.m3u8", "wb") as file:
#                     await file.write(await response.read())
#
#                 n = 1
#                 async with aiofiles.open("video.m3u8", mode="r", encoding="utf-8") as f:
#                     async for line in f:
#                         line = line.strip()
#                         if not line.startswith("#"):
#                             resp3 = await session.get(line)
#                             encrypted_data = await resp3.read()
#                             await download_video_segment(key, iv, encrypted_data, n)
#                             n += 1
#

# async def main():
#     base_url = "https://www.yitutrend.com/vp-ectid/v3-983203-"
#     num = 47
#     tasks = [download_one_page(f"{base_url}{i}.html", i) for i in range(2, num + 1)]
#     await asyncio.gather(*tasks)
#
#
# if __name__ == "__main__":
#     asyncio.run(main())

# 第一版：可行
# 第二版
import aiohttp
import asyncio
import aiofiles
from Crypto.Cipher import AES
import binascii
import re
from bs4 import BeautifulSoup

async def get_video_url(url):
    try:
        async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False)) as session:
            async with session.get(url, headers={'User-Agent': 'Mozilla/5.0'}) as response:
                if response.status != 200:
                    return None
                html = await response.text()
                bsObj = BeautifulSoup(html, 'html.parser')
                tag = bsObj.find('video').find('source')
                if tag:
                    return tag["src"]
                else:
                    return None
    except aiohttp.ClientError as e:
        print(f"An error occurred while fetching video url: {e}")
        return None

async def parse_m3u8_text(m3u8_text):
    try:
        m3u8_text = m3u8_text.split()
        encode_info = [line for line in m3u8_text if line.startswith('#EXT-X-KEY:')][0]

        pattern = r"#EXT-X-KEY:METHOD=(.*),URI=\"(.*)\",IV=(.*)"
        match = re.search(pattern, encode_info)
        if match:
            key_url = match.group(2)
            IV = match.group(3)[2:]
        else:
            raise Exception('Failed to parse m3u8 text')

        return key_url, IV
    except Exception as e:
        print(f"An error occurred while parsing m3u8 text: {e}")
        raise

async def download_video_segment(key, iv, encrypted_data, n):
    try:
        cipher = AES.new(key, AES.MODE_CBC, iv)
        decrypted_data = cipher.decrypt(encrypted_data)

        async with aiofiles.open(f'video_data_decrypted/{n}.ts', 'wb') as f:
            await f.write(decrypted_data)
        print(f"seg{n} is done.")
    except Exception as e:
        print(f"Error downloading video segment {n}: {e}")

async def download_one_page(url, i):
    m3u8_url = await get_video_url(url)
    if m3u8_url is None:
        return

    async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False)) as session:
        async with session.get(m3u8_url, verify_ssl=False) as response:
            if response.status != 200:
                print(f"Failed to download m3u8 file from {m3u8_url}")
                return

            m3u8_text = await response.text()

            try:
                key_url, IV = await parse_m3u8_text(m3u8_text)
                key_url = m3u8_url[:-10] + key_url
                key_response = await session.get(key_url)
                key = await key_response.read()
                iv = binascii.unhexlify(IV)

                async with aiofiles.open("video.m3u8", "wb") as file:
                    await file.write(await response.read())

                n = 1
                async with aiofiles.open("video.m3u8", mode="r", encoding="utf-8") as f:
                    async for line in f:
                        line = line.strip()
                        if not line.startswith("#"):
                            resp3 = await session.get(line)
                            encrypted_data = await resp3.read()
                            await download_video_segment(key, iv, encrypted_data, n)
                            n += 1
            except Exception as e:
                print(f"Error downloading page {i}: {e}")

async def main():
    base_url = "https://www.yitutrend.com/vp-ectid/v3-983203-"
    num = 47
    tasks = [download_one_page(f"{base_url}{i}.html", i) for i in range(2, num + 1)]
    await asyncio.gather(*tasks)

if __name__ == "__main__":
    asyncio.run(main())

