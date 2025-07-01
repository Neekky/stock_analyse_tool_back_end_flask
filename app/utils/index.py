import time
import requests
import datetime
import re
import json
import pandas as pd
import numpy as np
import ta

singleToday = datetime.datetime.now().strftime("%Y-%m-%d")

def requestForNew(url, max_try_num=10, sleep_time=5):
    headers = {
        'Referer': 'http://finance.sina.com.cn',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.71 Safari/537.36 Edg/97.0.1072.62'
    }
    for i in range(max_try_num):
        response = requests.get(url, headers=headers, timeout=30, verify=False)
        if response.status_code == 200:
            return response
        else:
            print("链接失败", response)
            time.sleep(sleep_time)

def requestForQKA(url, max_try_num=10, sleep_time=5):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/97.0.4692.71 Safari/537.36 Edg/97.0.1072.62'
    }
    for i in range(max_try_num):
        response = requests.get(url, headers=headers, timeout=30, verify=False)
        if response.status_code == 200:
            return response
        else:
            print("链接失败", response)
            time.sleep(sleep_time)


def getDate():
    url = 'https://hq.sinajs.cn/list=sh000001'
    response = requestForNew(url).text
    data_date = str(response.split(',')[-4])
    print(data_date, "data_date")
    # 获取上证的指数日期
    return data_date

def clean_key(key):
    # 使用正则表达式去除键名中的日期时间字符
    return re.sub(r'\[\d{8}\]', '', key)


def remove_field_from_objects(lst, key):
    """
    从列表中的每个对象中删除指定字段。

    参数：
    lst (list): 对象列表。
    key (str): 要删除的字段名称。

    返回：
    list: 处理后的列表。
    """
    if not isinstance(lst, list):
        raise TypeError("输入必须是一个列表")
    if not isinstance(key, str):
        raise TypeError("键必须是一个字符串")

    result = []
    for item in lst:
        if not isinstance(item, dict):
            # 假设对象是字典，如果不是，则跳过
            result.append(item)
            continue

        # 深复制，避免影响原列表
        new_item = dict(item)
        # 尝试删除指定字段
        new_item.pop(key, None)
        result.append(new_item)

    return result

# 将json数据中的key进行清理，将包含的日期去除掉，并转为字典类型，做为list的元素项
def clean_json(json_data):
    # 如果输入是字符串，需要先进行json解析
    if isinstance(json_data, str):
        json_data = json.loads(json_data)

    # 处理json数组中的每一个对象
    cleaned_data = []
    for item in json_data:
        cleaned_item = {}
        for key, value in item.items():
            new_key = clean_key(key)
            cleaned_item[new_key] = value
        cleaned_data.append(cleaned_item)

    return cleaned_data