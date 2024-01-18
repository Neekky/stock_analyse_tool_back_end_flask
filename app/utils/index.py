import time
import requests

def requestForNew(url, max_try_num=10, sleep_time=5):
    headers = {
        'Referer': 'http://finance.sina.com.cn',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.71 Safari/537.36 Edg/97.0.1072.62'
    }
    for i in range(max_try_num):
        response = requests.get(url, headers=headers, timeout=30)
        if response.status_code == 200:
            return response
        else:
            print("链接失败", response)
            time.sleep(sleep_time)