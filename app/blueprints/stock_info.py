import sys
sys.path.append('/usr/src/stock_analyse_tool_back_end_flask')
from flask import Blueprint, request, Response, jsonify
from app.models.stock_data import StockData
import pandas as pd
import akshare as ak
import datetime
from config import root_path
import pywencai
import json

singleToday = datetime.datetime.now().strftime("%Y%m%d")

stock_info_bp = Blueprint('stock_info', __name__, url_prefix='/stock_info')

# 个股的基本面怎么样
@stock_info_bp.route('/fundamentals', methods = ["GET"])
def get_stock_fundamentals():
    name = request.args.get("name") or ''

    if (not name):
        return 404
    query = '%s的基本面怎么样' % name

    # 首选方式问财
    res = pywencai.get(query=query)

    fundTxt = res['container']['fundTxt'].to_json(orient="records", force_ascii=False)
    evaluate = res['container']['txt1']
    capacity = res['container']['newRadar'].to_json(orient="records", force_ascii=False)

    print(type(fundTxt), 'res')

    res_dict = {
        'fundTxt': fundTxt,
        'evaluate': evaluate,
        'capacity': capacity
    }

    result = jsonify(res_dict)

    return result, 200, {'mimetype': 'application/json'}
