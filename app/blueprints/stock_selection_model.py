import sys

from app.utils.index import clean_json, remove_field_from_objects

sys.path.append('/usr/src/stock_analyse_tool_back_end_flask')
import pandas as pd
import akshare as ak
import datetime
from config import root_path
from flask import Blueprint, request
import time
import os
import glob

singleToday = datetime.datetime.now().strftime("%Y%m%d")
singleToday2 = datetime.datetime.now().strftime("%Y-%m-%d")

stock_selection_model_bp = Blueprint('stock_selection_model', __name__, url_prefix='/stock_selection_model')

# 获取涨停kdj数据
@stock_selection_model_bp.route('/get_limit_kdj_model_data', methods=['GET'])
def get_limit_kdj_model_data():
    try:
        date = request.args.get("date") or singleToday
        # 根据日期，找到对应的数据进行返回
        base_path = root_path + '/stock_analyse_tool_data_crawl/database/自研问句/' + date + '/kdj金叉涨停.csv'

        df = pd.read_csv(base_path)

        result = df.to_json(orient="records", force_ascii=False)

        # 处理数据
        cleaned_data = clean_json(result)

        cleaned_data = remove_field_from_objects(cleaned_data, '涨停明细数据')

        response = {
            'code': 200,
            'data': cleaned_data,
            'msg': '请求成功'
        }
        return response
    except Exception as e:
        response = {
            'code': 500,
            'data': [],
            'msg': '请求发生错误'
        }
        return response


# 获取涨停的概念龙头数据
@stock_selection_model_bp.route('/get_limit_leading_model_data', methods=['GET'])
def get_limit_leading_model_data():
    try:
        date = request.args.get("date") or singleToday
        # 根据日期，找到对应的数据进行返回
        base_path = root_path + '/stock_analyse_tool_data_crawl/database/自研问句/' + date + '/涨停龙头.csv'

        df = pd.read_csv(base_path)

        result = df.to_json(orient="records", force_ascii=False)

        # 处理数据
        cleaned_data = clean_json(result)

        cleaned_data = remove_field_from_objects(cleaned_data, '涨停明细数据')

        response = {
            'code': 200,
            'data': cleaned_data,
            'msg': '请求成功'
        }
        return response
    except Exception as e:
        response = {
            'code': 500,
            'data': [],
            'msg': '请求发生错误'
        }
        return response
    

# 获取符合缩量条件的股票数据
@stock_selection_model_bp.route('/get_volume_decrease_data_backup', methods=['GET'])
def get_volume_decrease_data():
    try:
        date = request.args.get("date") or singleToday2
        
        # 构建基础路径
        base_dir = root_path + '/stock_analyse_tool_data_crawl/database/每日日报/'
        target_path = os.path.join(base_dir, date, '缩量优选.csv')
        
        # 读取目标日期的数据
        df = pd.read_csv(target_path, dtype={'代码': str})
        df['代码'] = df['代码'].astype(str).str.zfill(6)
        
        # 获取所有可用的日期文件夹
        all_dates = []
        date_folders = glob.glob(os.path.join(base_dir, '*'))
        for folder in date_folders:
            folder_name = os.path.basename(folder)
            if folder_name.isdigit() and len(folder_name) == 8:  # 检查是否为8位数字日期
                all_dates.append(folder_name)
        
        # 按日期排序
        all_dates.sort()
        
        # 找到当前日期在列表中的位置
        if date in all_dates:
            date_index = all_dates.index(date)
            # 获取前两个交易日（如果存在）
            previous_dates = []
            if date_index >= 1:
                previous_dates.append(all_dates[date_index-1])
            if date_index >= 2:
                previous_dates.append(all_dates[date_index-2])
        else:
            previous_dates = []
        
        # 读取前两日的数据
        previous_codes = set()
        for prev_date in previous_dates:
            prev_path = os.path.join(base_dir, prev_date, '缩量优选.csv')
            if os.path.exists(prev_path):
                try:
                    df_prev = pd.read_csv(prev_path, dtype={'代码': str})
                    df_prev['代码'] = df_prev['代码'].astype(str).str.zfill(6)
                    previous_codes.update(df_prev['代码'].tolist())
                except Exception as e:
                    print(f"读取{prev_date}数据失败: {e}")
        
        # 过滤掉在前两日出现过的股票代码
        if previous_codes:
            mask = ~df['代码'].isin(previous_codes)
            df = df[mask].reset_index(drop=True)
        
        result = df.to_json(orient="records", force_ascii=False)
        
        # 处理数据
        cleaned_data = clean_json(result)
        
        response = {
            'code': 200,
            'data': cleaned_data,
            'msg': '请求成功',
            'previous_dates': previous_dates,
            'filtered_count': len(previous_codes)
        }
        return response
    except Exception as e:
        print(f"处理缩量优选数据时发生错误: {e}")
        response = {
            'code': 500,
            'data': [],
            'msg': f'请求发生错误: {str(e)}'
        }
        return response

# 获取符合缩量条件的股票数据
@stock_selection_model_bp.route('/get_volume_decrease_data', methods=['GET'])
def get_volume_decrease_data():
    try:
        date = request.args.get("date") or singleToday2
        # 根据日期，找到对应的数据进行返回
        base_path = root_path + '/stock_analyse_tool_data_crawl/database/每日日报/' + date + '/缩量优选.csv'

        # 读取CSV文件时指定股票编码列为字符串类型，防止前导零丢失
        df = pd.read_csv(base_path, dtype={'代码': str})
        
        # 确保股票代码为6位数字符串，补全前导零
        df['代码'] = df['代码'].astype(str).str.zfill(6)

        result = df.to_json(orient="records", force_ascii=False)

        # 处理数据
        cleaned_data = clean_json(result)

        response = {
            'code': 200,
            'data': cleaned_data,
            'msg': '请求成功'
        }
        return response
    except Exception as e:
        response = {
            'code': 500,
            'data': [],
            'msg': '请求发生错误'
        }
        return response

# 获取见底的etf数据
@stock_selection_model_bp.route('/get_etf_data', methods=['GET'])
def get_bottom_etf_model_data():
    symbol = request.args.get("symbol")
    if not symbol:
        return {"code": 400, "msg": "Symbol is required"}, 400

    max_retries = 3
    wait_time = 2

    for retry in range(max_retries):
        try:
            df = ak.fund_etf_hist_em(
                symbol=symbol,
                period="daily",
                end_date=singleToday,
                adjust="qfq"
            )
            if df.empty:
                if retry == max_retries - 1:
                    return {"code": 404, "msg": "No data found for the given symbol"}, 404
                print(f"No data found. Retrying {retry + 1}/{max_retries}...")
                time.sleep(wait_time)
                continue

            json_data = df.to_json(orient="records", force_ascii=False)
            return {
                'data': json_data,
                'code': 200,
                'msg': '成功'
            }, 200

        except Exception as e:
            if retry == max_retries - 1:
                print(f"Max retries reached. Error: {e}")
                return {"code": 500, "msg": "Internal server error"}, 500
            print(f"Error occurred: {e}. Retrying {retry + 1}/{max_retries}...")
            time.sleep(wait_time)

    # This line should never be reached, but just in case
    return {"code": 500, "msg": "Unexpected error occurred"}, 500

