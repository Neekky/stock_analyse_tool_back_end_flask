import time
import requests
import re
import json
import pandas as pd
import numpy as np

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

# 分析趋势
def analyze_trend(df):
    # 检查是否DataFrame为空
    if df.empty:
        raise ValueError("DataFrame is empty")

    # 检查必须的列是否存在
    required_columns = ['candle_end_time', 'open', 'close', 'high', 'low', 'amount']
    for column in required_columns:
        if column not in df.columns:
            raise ValueError(f"缺少必要的列: {column}")

    # 按日期升序排序（最新一天在最后）
    df = df.sort_values(by='candle_end_time')

    # 连续上涨天数和连续下跌天数初始化为0
    consecutive_up_days = 0
    consecutive_down_days = 0

    # 从最新一天往前分析
    for i in range(len(df) - 1, 0, -1):
        if df.iloc[i]['close'] > df.iloc[i - 1]['close']:
            if consecutive_down_days > 0:
                break
            consecutive_up_days += 1
        elif df.iloc[i]['close'] < df.iloc[i - 1]['close']:
            if consecutive_up_days > 0:
                break
            consecutive_down_days += 1
        else:
            break  # 如果close相等，则停止分析

    return consecutive_up_days, consecutive_down_days


def latest_change_percentage(df):
    """计算最新一天的涨跌幅"""
    latest_close = df['close'].iloc[-1]
    previous_close = df['close'].iloc[-2]
    change_percentage = (latest_close - previous_close) / previous_close * 100
    return change_percentage

def detect_trend(df, period=22):
    """检测趋势，默认为14天的趋势"""
    trend_df = df.tail(period)
    trend_close = trend_df['close'].values
    x = np.arange(len(trend_close))
    # 对收盘价做线性回归，看斜率
    slope = np.polyfit(x, trend_close, 1)[0]

    # 设置阈值
    theta_up = 0.5
    theta_down = -0.5

    print(slope, 'slope')
    if slope > theta_up:
        return "上行趋势"
    elif slope < theta_down:
        return "下行趋势"
    else:
        return "横盘震荡"

def detect_reversal(latest_change, current_trend):
    """判断是否为加速趋势"""

    """判断是否反转趋势"""
    if current_trend == "上行趋势" and latest_change < -1:
        return True
    elif current_trend == "下行趋势" and latest_change > 1:
        return True
    else:
        return False

def detect_speed_up(latest_change, current_trend):
    """判断是否为加速趋势"""
    if current_trend == "上行趋势" and latest_change > 1.5:
        return '加速上涨'
    elif current_trend == "下行趋势" and latest_change < -1.5:
        return '加速下跌'
    else:
        return '趋势延续'

def analyze_index(df):
    """综合分析指数运行情况"""
    if len(df) < 2:
        raise ValueError("DataFrame行数不足以进行分析")

    latest_change = latest_change_percentage(df)

    trend = detect_trend(df)

    is_reversal = detect_reversal(latest_change, trend)

    is_speed_up = detect_speed_up(latest_change, trend)

    is_significant = False

    if abs(latest_change) > 1.5:  # 这里以2%为界限，可以根据需求调整
        is_significant = True
    else:
        is_significant = False

    return {
        "最新涨跌幅": latest_change,
        "当前趋势": trend,
        "是否反转": is_reversal,
        "是否剧烈振幅": is_significant,
        "是否加速": is_speed_up
    }

# result = analyze_index(df)
# print(result)


# 获取沪深300指数，分析赛道股、题材股的反比情况。可以做成实时分析，10秒频次的获取，分析市场动向。
# 分析涨家数、跌家数。成交量，判断市场情绪。有一个通过当前成交量、历史成交量区间的东西，判断当前市场是否过热，是否低迷。
