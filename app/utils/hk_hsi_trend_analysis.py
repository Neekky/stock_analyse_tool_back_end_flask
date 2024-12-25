import pandas as pd
import numpy as np
import ta
import matplotlib.pyplot as plt
import json
from scipy.stats import linregress
from sklearn.linear_model import LinearRegression
import datetime

from app.utils.common_config import prodPath
from config import root_path

pd.set_option('expand_frame_repr', False)  # 当列太多时不换行
pd.set_option('display.max_rows', 10000)  # 最多显示数据的行数
# 设置命令行输出时的列对齐功能
pd.set_option('display.unicode.ambiguous_as_wide', True)
pd.set_option('display.unicode.east_asian_width', True)

singleToday = datetime.datetime.now().strftime("%Y-%m-%d")


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


# 辅助df累计函数
def helpCounter(df, newColName, counterCol):
    """
       辅助df累计函数

       参数:
       mynewdf: 要处理的df。
       newColName: 要新增的列名。
       counterCol: 要累加的列名

       返回:
       df: 两个加数的和。
    """
    mynewdf = df.copy()
    # 缩量信号的累计
    mynewdf['连续计数'] = (mynewdf[counterCol] != mynewdf[counterCol].shift()).cumsum()  # 用来识别每一段连续的信号
    mynewdf[newColName] = mynewdf.groupby('连续计数')[counterCol].cumsum()  # 按照每一段进行累加

    # 删除辅助列
    mynewdf = mynewdf.drop(columns=['连续计数'])

    return mynewdf


# 数据预处理
def data_pre(df):
    mynewdf = df.copy()

    # 计算移动平均线（MA）
    mynewdf.loc[:, 'MA8'] = mynewdf['close'].rolling(window=8).mean()
    mynewdf.loc[:, 'MA20'] = mynewdf['close'].rolling(window=20).mean()
    mynewdf.loc[:, 'MA50'] = mynewdf['close'].rolling(window=50).mean()

    # 计算相对强弱指数（RSI）
    mynewdf.loc[:, 'RSI'] = ta.momentum.RSIIndicator(mynewdf['close'], window=12).rsi()
    mynewdf.loc[:, 'RSI6'] = ta.momentum.RSIIndicator(mynewdf['close'], window=6).rsi()

    # 计算rsi的金叉死叉数据
    mynewdf.loc[:, 'RSI_Cross'] = (mynewdf['RSI6'] > mynewdf['RSI']).astype(int)

    # mynewdf.loc[:, 'RSI24'] = ta.momentum.RSIIndicator(mynewdf['close'], window=24).rsi()

    # 计算指数的MACD
    # mynewdf.loc[:, 'MACD'] = ta.trend.macd(close=mynewdf['close'], window_slow=26, window_fast=12, fillna=True)
    # mynewdf.loc[:, 'MACD_signal'] = ta.trend.macd_signal(close=mynewdf['close'], window_slow=26, window_fast=12, window_sign=9, fillna=True)
    # mynewdf.loc[:, 'MACD_diff'] = ta.trend.macd_diff(close=mynewdf['close'], window_slow=26, window_fast=12, window_sign=9, fillna=True)

    # 计算MACD 5日均线
    # mynewdf.loc[:, 'MACD_MA5'] = mynewdf['MACD'].rolling(window=3).mean()
    # mynewdf.loc[:, 'MACD_less_than_MA5'] = (mynewdf['MACD'] < mynewdf['MACD_MA5']).astype(int)
    #
    # print(mynewdf[['candle_end_time', 'MACD', 'MACD_signal', 'MACD_diff', 'MACD_MA5', 'MACD_less_than_MA5']])


    # 计算成交量的移动平均
    mynewdf.loc[:, 'Volume_MA20'] = mynewdf['amount'].rolling(window=20).mean()

    # 计算成交量5日移动平均
    mynewdf.loc[:, 'Volume_MA5'] = df['amount'].rolling(window=5).mean()

    # 5日涨跌幅
    mynewdf.loc[:, '5d_change'] = mynewdf['close'].pct_change(periods=5) * 100

    # 5日成交量是否缩量
    mynewdf.loc[:, 'is_5d_volume_decreasing'] = (mynewdf['amount'] < mynewdf['Volume_MA5']).astype(int)

    # 计算5日成交量是否缩量的信号累加
    mynewdf = helpCounter(mynewdf, '5日缩量信号累加', 'is_5d_volume_decreasing')

    return mynewdf


def latest_change_percentage(df):
    """计算最新一天的涨跌幅"""
    latest_close = df['close'].iloc[-1]
    previous_close = df['close'].iloc[-2]
    change_percentage = (latest_close - previous_close) / previous_close * 100
    return change_percentage


def detect_trend_opt(df, period=22):
    """检测趋势，默认为14天的趋势"""
    trend_df = df.tail(period)
    trend_close = trend_df['close'].values
    x = np.arange(len(trend_close))
    # 对收盘价做线性回归，看斜率
    slope = np.polyfit(x, trend_close, 1)[0]

    # 设置阈值
    theta_up = 0.5
    theta_down = -0.5

    if slope > theta_up:
        return "上行趋势"
    elif slope < theta_down:
        if theta_down < -5:
            # 这个判断看看咋回事
            return '极速下行'
        else:
            return "下行趋势"
    else:
        return "横盘震荡"


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

    if slope > theta_up:
        return "上行趋势"
    elif slope < theta_down:
        if theta_down < -5:
            # 这个判断看看咋回事
            return '极速下行'
        else:
            return "下行趋势"
    else:
        return "横盘震荡"


# 分析指数是否见顶见底反转的概率
def detect_reversal(selfdf, trend):
    # 数据预处理
    drdf = data_pre((selfdf)).copy()

    # 最新收盘价
    latest_close = drdf['close'].iloc[-1]
    # 最新成交量
    latest_vol = drdf['amount'].iloc[-1]
    # 价格8日线
    latest_ma8 = drdf['MA8'].iloc[-1]
    # 价格20日线
    latest_ma20 = drdf['MA20'].iloc[-1]
    # 价格50日线
    latest_ma50 = drdf['MA50'].iloc[-1]
    # 最新12日rsi
    latest_rsi = drdf['RSI'].iloc[-1]
    # 成交量20日线
    latest_vol_ma20 = drdf['Volume_MA20'].iloc[-1]
    # 5日涨跌幅
    latest_5d_change = drdf['5d_change'].iloc[-1]
    # 是否缩量信号的累加值
    latest_5d_volume_decreasing_counter = drdf['5日缩量信号累加'].iloc[-1]

    # RSI当前为金叉还是死叉
    latest_rsi_cross = drdf['RSI_Cross'].iloc[-1]

    # 5日内最大振幅
    last_5_days = drdf['close'][-6:]  # 获取最近5日的收盘价
    max_price = last_5_days.max()  # 最大值
    min_price = last_5_days.min()  # 最小值
    amplitude = (max_price - min_price) / min_price * 100  # 计算振幅

    score = 0
    score_map = ''

    if (trend == '上行趋势'):
        # 价格上穿20日均线
        if (latest_close > latest_ma20):
            score += 10
            score_map += '价格上穿20日均线 ->'

        # 价格20日均线上穿50日均线
        if (latest_ma20 > latest_ma50):
            score += 10
            score_map += '价格20日均线上穿50日均线 ->'

        if (latest_rsi > 70):
            score += 10
            score_map += 'rsi大于70 ->'

        if (latest_close < latest_ma8):
            score += 10
            score_map += '最新价格跌破5日线 ->'

        # 加速上涨，加速赶顶
        if (amplitude > 3 and latest_5d_change > 0):
            score += 10
            score_map += '加速上涨加速赶顶 ->'

        # 高位成交量放大
        if (latest_vol > latest_vol_ma20):
            score += 10
            score_map += '高位成交量放大 ->'

        # rsi死叉
        if (latest_rsi_cross == 0):
            score += 10
            score_map += 'rsi死叉 ->'

    else:
        # 价格跌破20日均线
        if (latest_close < latest_ma20):
            score -= 10
            score_map += '价格跌破20日均线 ->'

        # 价格20日均线跌破50日均线
        if (latest_ma20 < latest_ma50):
            score -= 10
            score_map += '价格20日均线跌破50日均线 ->'

        if (latest_rsi < 30):
            score -= 10
            score_map += 'rsi小于30 ->'

        if (latest_ma20 < latest_ma8):
            score += 10
            score_map += '8日线大于20日线 ->'

        # 加速下跌，加速赶底
        if (amplitude > 4 and latest_5d_change < 0):
            score -= 10
            score_map += '加速下跌加速赶底 ->'

        # 低位成交量放大
        if (latest_vol > latest_vol_ma20):
            score -= 10
            score_map += '低位成交量放大 ->'

        # rsi金叉
        if (latest_rsi_cross == 1):
            score -= 10
            score_map += 'rsi金叉 ->'

    percent = abs(score / 70 * 100)
    # print(score, percent, score_map)
    # 转换为百分制
    return {
        'score': f"{score:.2f}",
        'percent': f"{percent:.2f}",
        'score_map': score_map,
        'volume_ma5_decreasing_counter': int(latest_5d_volume_decreasing_counter),  # 下跌情况，缩量可能更为重要
    }


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

    is_reversal = detect_reversal(df, trend)

    is_speed_up = detect_speed_up(latest_change, trend)

    is_significant = False

    if abs(latest_change) > 1.5:  # 这里以2%为界限，可以根据需求调整
        is_significant = True
    else:
        is_significant = False

    return {
        "最新涨跌幅": latest_change,
        "当前趋势": trend,
        "反转数据": is_reversal,
        "是否剧烈振幅": is_significant,
        "是否加速": is_speed_up
    }


# 批量处理趋势分析，回测日期区间数据
def batching_data(mydf, date):
    new_df = mydf[mydf['date'] <= date]

    trend = detect_trend(new_df)

    is_reversal = detect_reversal(new_df, trend)

    return is_reversal['score']


# 批处理函数入口
def hk_hsi_batching_entry(code='hkHSI', start_date='2022-05-11', end_date=singleToday):
    base_path = root_path + prodPath + '/stock_data_base/data/指数历史日线数据/%s.csv' % code

    # 使用示例数据进行测试 520
    df = pd.read_csv(base_path)
    df2 = pd.read_csv(base_path)

    df = df.rename(columns={'开盘': 'open', '收盘': 'close', '最高': 'high', '最低': 'low', '成交量': 'amount',
                            '日期': 'candle_end_time'})
    df2 = df2.rename(columns={'开盘': 'open', '收盘': 'close', '最高': 'high', '最低': 'low', '成交量': 'amount',
                             '日期': 'candle_end_time'})

    df['date'] = pd.to_datetime(df['candle_end_time'])
    df2['date'] = pd.to_datetime(df2['candle_end_time'])

    mask = (df['date'] <= end_date) & (df['date'] >= start_date)

    df = df[mask]

    date_list = df['candle_end_time'].tolist()
    # 用于存储函数返回值的列表
    results = []

    # 遍历日期列表
    for date in date_list:
        # 动态更新 df
        score = batching_data(df2, date)  # 将返回值添加到结果列表

        results.append(score)

    resdf = pd.DataFrame({
        'date': date_list,
        'score': results
    })

    resdf['score'] = resdf['score'].astype(float)

    resdf['percent'] = resdf['score'] / 70 * 100

    return resdf