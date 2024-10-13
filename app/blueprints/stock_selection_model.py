import sys

from app.utils.common_config import prodPath
from app.utils.index import clean_json, remove_field_from_objects

sys.path.append('/usr/src/stock_analyse_tool_back_end_flask')
import pandas as pd
import akshare as ak
import datetime
from config import root_path
import pywencai
import json
from flask import Blueprint, jsonify, request
from app.models import db
from app.models.stock_limit_movement import StockLimitMovement
import time

singleToday = datetime.datetime.now().strftime("%Y%m%d")

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


