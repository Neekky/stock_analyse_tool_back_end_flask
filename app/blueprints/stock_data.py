import os
import sys
import pywencai

from app.utils.trend_analysis import analyze_trend, analyze_index, batching_entry

sys.path.append('/usr/src/stock_analyse_tool_back_end_flask')
from flask import Blueprint
from app.models.stock_data import StockData
from flask import request
import pandas as pd
import akshare as ak
import datetime
from config import root_path

singleToday = datetime.datetime.now().strftime("%Y%m%d")

stock_data_bp = Blueprint('stock_data', __name__)

# todo调试时设置为quant，发布时改为空
prodPath = ''

# 获取个股股票K线
@stock_data_bp.route('/get_stock_k_line', methods=["GET"])
def get_stock_k_line():  # put application's code here
    # 可以通过 request 的 args 属性来获取参数
    symbol = request.args.get("symbol") or ''

    if (not symbol):
        return 404

    period = request.args.get("period") or 'daily'
    start_date = request.args.get("start_date") or ''
    adjust = request.args.get("adjust") or ''
    end_date = request.args.get("end_date") or ''
    is_head_end = request.args.get("is_head_end")

    stock_zh_a_hist_df = ak.stock_zh_a_hist(symbol=symbol + '', period=period + '', start_date=start_date + '',
                                            end_date=end_date + '', adjust=adjust + '')
    # 如果is_head_end为1，则只保留第一行和最后一行
    if (is_head_end == '1' and stock_zh_a_hist_df.shape[0] > 1):
        # 只保留stock_zh_a_hist_df的第一行和最后一行
        stock_zh_a_hist_df = stock_zh_a_hist_df.iloc[[0, -1]]

    response = stock_zh_a_hist_df.to_json(orient="records", force_ascii=False)
    return response


# 获取指数K线
@stock_data_bp.route('/get_index_k_line', methods=["GET"])
def get_index_k_line():  # put application's code here
    # 可以通过 request 的 args 属性来获取参数
    index = request.args.get("index") or 'sh000001'
    startDate = request.args.get("startDate") or None
    endDate = request.args.get("endDate") or None

    # todo 定义指数文件路径,本地开发这里要加quant
    base_path = root_path + prodPath + '/stock_data_base/data/指数历史日线数据/' + index + '.csv'
    df = pd.read_csv(base_path)
    df['date'] = pd.to_datetime(df['candle_end_time'])

    if (startDate):
        df = df[df['date'] >= startDate]
    if (endDate):
        df = df[df['date'] <= endDate]

    result = df.to_json(orient="records", force_ascii=False)
    response = {
        'code': 200,
        'data': result,
        'msg': '请求成功'
    }
    return response


# 获取指数的见顶见底概率
@stock_data_bp.route('/get_index_top_bottom_percent', methods=["GET"])
def get_index_top_bottom_percent():
    type = request.args.get("type") or 'index'
    code = request.args.get("code") or 'sh000001'
    start_date = request.args.get("start_date") or '2022-05-11'
    end_date = request.args.get("end_date") or singleToday
    resdf = batching_entry(type, code, start_date, end_date)
    result = resdf.to_json(orient="records", force_ascii=False)
    response = {
        'code': 200,
        'data': result,
        'msg': '请求成功'
    }
    return response

# 获取每日涨停数据
@stock_data_bp.route('/get_limitup_rank', methods=["GET"])
def get_limitup_rank():
    start_date = request.args.get("start_date") or None

    if (not start_date):
        return '500'

    df = pd.read_csv(root_path + '/stock_analyse_tool_data_crawl/database/每日涨停/%s/今日涨停.csv' % start_date)
    df['涨停封单额排名'] = df['涨停封单额[%s]' % start_date].rank(ascending=False, method='min')
    df['涨停开板次数排名'] = df['涨停开板次数[%s]' % start_date].rank(ascending=True, method='dense')
    df['最终涨停时间排名'] = df['最终涨停时间[%s]' % start_date].rank(ascending=True, method='dense')
    df['连续涨停天数排名'] = df['连续涨停天数[%s]' % start_date].rank(ascending=True, method='dense')
    df['a股市值排名'] = df['a股市值(不含限售股)[%s]' % start_date].rank(ascending=True, method='dense')

    df['复合因子'] = df['涨停封单额排名'] + df['涨停开板次数排名'] + df['最终涨停时间排名'] + df['连续涨停天数排名'] + \
                     df['a股市值排名']

    # 对因子进行排名
    df['排名'] = df['复合因子'].rank(method="first")
    response = df.to_json(orient="records", force_ascii=False)
    return response


@stock_data_bp.route('/get_winners_list', methods=["GET"])
def get_winners_list():
    start_date = request.args.get("start_date") or None
    end_date = request.args.get("end_date") or None
    if (not start_date or not end_date):
        return '500'
    stock_lhb_detail_em_df = ak.stock_lhb_detail_em(start_date=start_date, end_date=end_date)
    df_combined = stock_lhb_detail_em_df.groupby('代码').agg({
        '名称': 'first',
        '上榜日': 'first',
        '解读': 'first',
        '收盘价': 'first',
        '涨跌幅': 'first',
        '龙虎榜净买额': 'first',
        '龙虎榜买入额': 'first',
        '龙虎榜卖出额': 'first',
        '龙虎榜成交额': 'first',
        '市场总成交额': 'first',
        '净买额占总成交比': 'first',
        '成交额占总成交比': 'first',
        '换手率': 'first',
        '流通市值': 'first',
        '上榜原因': list,
        '上榜后1日': 'first',
        '上榜后2日': 'first',
        '上榜后5日': 'first',
        '上榜后10日': 'first',
    }).reset_index()
    df_combined = df_combined[~df_combined['名称'].str.endswith('转债')]
    df_combined = df_combined[~df_combined['代码'].str.startswith('8')]
    df_combined['code'] = df_combined['代码']
    response = df_combined.to_json(orient="records", force_ascii=False)
    return response


@stock_data_bp.route('/get_early_strategy_data', methods=["GET"])
def get_early_strategy_data():
    start_date = request.args.get("start_date") or None

    if (not start_date):
        return '500'

    df = pd.read_csv(root_path + '/stock_analyse_tool_data_crawl/database/自研问句/%s/竞价连板筛选.csv' % start_date)
    response = df.to_json(orient="records", force_ascii=False)
    return response

# 获取指数运行状态
@stock_data_bp.route('/get_status_of_index', methods=["GET"])
def get_status():
    index = request.args.get("index") or 'sh000001'

    # todo 定义指数文件路径,本地开发这里要加quant
    base_path = root_path + prodPath + '/stock_data_base/data/指数历史日线数据/' + index + '.csv'
    # 使用示例数据进行测试 520
    df = pd.read_csv(base_path)
    consecutive_up_days, consecutive_down_days = analyze_trend(df)

    result = analyze_index(df)
    resData = {
        'consecutive_up_days': consecutive_up_days,
        'consecutive_down_days': consecutive_down_days,
        'index': index,
        **result
    }
    response = {
        'data': resData,
        'msg': '请求成功',
        'code': 200
    }

    return response, 200

# 获取今日昨日涨停板晋级情况
@stock_data_bp.route('/get_limitup_diff', methods=["GET"])
def get_limitup_diff():
    date = request.args.get("date") or None

    if (not date):
        return '500'

    # 假设csv文件夹的路径如下
    base_path = root_path + '/stock_analyse_tool_data_crawl/database/每日涨停/'

    # 读取文件夹下所有的子文件夹名称（日期）
    available_dates = [name for name in os.listdir(base_path)
                       if os.path.isdir(os.path.join(base_path, name))]

    # 保证日期列表有序，以便查找前一天的数据
    available_dates.sort()

    # 找到目标日期在列表中的索引位置
    try:
        current_index = available_dates.index(date)
    except ValueError:
        print(f"No data found for the target date: {date}")
        current_index = None

    if current_index is not None:
        current_date_str = available_dates[current_index]

        previous_date_str = available_dates[current_index - 1]

        # 拼接目标日期的CSV数据地址
        target_path = base_path
        limitup_1_path = target_path + current_date_str + '/1板.csv'
        limitup_2_path = target_path + current_date_str + '/2板.csv'
        limitup_3_path = target_path + current_date_str + '/3板.csv'
        limitup_4_path = target_path + current_date_str + '/4板.csv'

        # 拼接目标前一日日期的CSV数据地址
        limitup_1_pre_path = target_path + previous_date_str + '/1板.csv'
        limitup_2_pre_path = target_path + previous_date_str + '/2板.csv'
        limitup_3_pre_path = target_path + previous_date_str + '/3板.csv'
        limitup_4_pre_path = target_path + previous_date_str + '/4板.csv'

        l1df = read_csv_with_fallback(limitup_1_path)
        l2df = read_csv_with_fallback(limitup_2_path)
        l3df = read_csv_with_fallback(limitup_3_path)
        l4df = read_csv_with_fallback(limitup_4_path)

        l1pdf = read_csv_with_fallback(limitup_1_pre_path)
        l2pdf = read_csv_with_fallback(limitup_2_pre_path)
        l3pdf = read_csv_with_fallback(limitup_3_pre_path)
        l4pdf = read_csv_with_fallback(limitup_4_pre_path)

        try:
            oneToTwoRate = round(l2df.shape[0] / l1pdf.shape[0] * 100)
        except Exception as e:  # 捕获所有可能的异常
            oneToTwoRate = round(l2df.shape[0] * 100)

        try:
            twoToThreeRate = round(l3df.shape[0] / l2pdf.shape[0] * 100)
        except Exception as e:  # 捕获所有可能的异常
            twoToThreeRate = round(l3df.shape[0] * 100)

        # 处理更多板，需要将重复的去掉
        try:
            merged_df = l4df.merge(l4pdf, how='outer', on='股票简称', indicator=True)
            filtered_df_A = merged_df[merged_df['_merge'] == 'left_only'].drop(columns=['_merge'])
            threeToMoreRate = round(filtered_df_A.shape[0] / l3pdf.shape[0] * 100)
        except Exception as e:  # 捕获所有可能的异常
            threeToMoreRate = round(filtered_df_A.shape[0] * 100)

        try:
            # 计算一板数量增减幅度
            oneRate = round((l1df.shape[0] - l1pdf.shape[0]) / l1df.shape[0] * 100)
        except Exception as e:  # 捕获所有可能的异常
            oneRate = round((l1df.shape[0] - l1pdf.shape[0]) * 100)

        resMap = {
            'oneCount': l1df.shape[0],
            'oneToTwoRate': oneToTwoRate,
            'oneToTwoCount': l2df.shape[0],
            'oneRate': oneRate,
            'twoToThreeRate': twoToThreeRate,
            'twoToThreeCount': l3df.shape[0],
            'threeToMoreRate': threeToMoreRate,
            'threeToMoreCount': l4df.shape[0],
            'yestdOneCount': l1pdf.shape[0],
            'yestdTwoCount': l2pdf.shape[0],
            'yestdThreeCount': l3pdf.shape[0],
            'yestdMoreCount': l4pdf.shape[0],
        }
        data = {
            'data': resMap,
            'code': 200,
        }

        return data, 200

    return 500

def read_csv_with_fallback(file_path):
    try:
        # 尝试读取CSV文件
        df = pd.read_csv(file_path)
    except Exception as e:  # 捕获所有可能的异常
        print(f"Error reading {file_path}: {e}")  # 打印错误信息
        df = pd.DataFrame()  # 创建一个空的DataFrame
    return df
