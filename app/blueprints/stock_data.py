import os
import sys
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

# 获取个股股票K线
@stock_data_bp.route('/get_stock_k_line', methods = ["GET"])
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

    stock_zh_a_hist_df = ak.stock_zh_a_hist(symbol=symbol + '', period=period + '', start_date=start_date + '', end_date=end_date + '', adjust=adjust + '')
    # 如果is_head_end为1，则只保留第一行和最后一行
    if (is_head_end == '1' and stock_zh_a_hist_df.shape[0] > 1):
        # 只保留stock_zh_a_hist_df的第一行和最后一行
        stock_zh_a_hist_df = stock_zh_a_hist_df.iloc[[0, -1]]

    response = stock_zh_a_hist_df.to_json(orient="records", force_ascii=False)
    return response

# 获取每日涨停数据
@stock_data_bp.route('/get_limitup_rank', methods = ["GET"])
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

    df['复合因子'] = df['涨停封单额排名'] + df['涨停开板次数排名'] + df['最终涨停时间排名'] + df['连续涨停天数排名'] + df['a股市值排名']

    # 对因子进行排名
    df['排名'] = df['复合因子'].rank(method="first")
    response = df.to_json(orient="records", force_ascii=False)
    return response

@stock_data_bp.route('/get_winners_list', methods = ["GET"])
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

@stock_data_bp.route('/get_early_strategy_data', methods = ["GET"])
def get_early_strategy_data():
    start_date = request.args.get("start_date") or None

    if (not start_date):
        return '500'
    
    df = pd.read_csv(root_path + '/stock_analyse_tool_data_crawl/database/自研问句/%s/竞价连板筛选.csv' % start_date)
    response = df.to_json(orient="records", force_ascii=False)
    return response

@stock_data_bp.route('/get_limitup_diff', methods = ["GET"])
def get_limitup_diff():
    date = request.args.get("date") or None

    if (not date):
        return '500'

    # 假设csv文件夹的路径如下
    base_path = root_path + '/stock_analyse_tool_data_crawl/database/每日涨停'

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
        # 读取目标日期的CSV数据
        target_path = base_path
        limitup_1_path = target_path + '/1板.csv'
        limitup_2_path = target_path + '/2板.csv'
        limitup_3_path = target_path + '/3板.csv'
        limitup_4_path = target_path + '/4板.csv'

        target_data = read_csv_data(target_path)

        # 查找并读取上一有效日期的CSV数据
        previous_data = None
        for previous_index in range(current_index - 1, -1, -1):
            previous_date_str = available_dates[previous_index]
            previous_path = os.path.join(base_path, previous_date_str)
            limitup_1_previous_path = previous_path + '/1板.csv'
            previous_data = read_csv_data(limitup_1_previous_path)

            print(previous_date_str)
            if previous_data is not None:
                break

        # 在这里，你可以进行数据处理，例如合并两天的数据
        if previous_data is not None and target_data is not None:
            # combined_data = pd.concat([previous_data, target_data])
            # 使用combined_data进行后续的数据处理
            return previous_data
        else:
            print("Unable to find data for the previous working day.")

# 定义一个函数来读取指定路径下所有CSV文件的数据
def read_csv_data(folder_path):
    all_files = os.listdir(folder_path)
    data_frames = []
    for file_name in all_files:
        if file_name.endswith('.csv'):
            file_path = os.path.join(folder_path, file_name)
            df = pd.read_csv(file_path)
            data_frames.append(df)
    return pd.concat(data_frames) if data_frames else None