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

all_info_bp = Blueprint('stock_info', __name__, url_prefix='/all_info')

# 个股的基本面怎么样
@all_info_bp.route('/fundamentals', methods = ["GET"])
def get_stock_fundamentals():
    name = request.args.get("name") or ''

    if (not name):
        return 404
    query = '%s的基本面怎么样' % name

    # 首选方式问财
    res = pywencai.get(query=query)

    print(res.keys(), res['行业排名'].keys(), res['行业排名']['营业收入'])

    fundTxt = res['container']['fundTxt'].to_json(orient="records", force_ascii=False)
    evaluate = res['txt1']
    capacity = res['txt2']
    baseView = res['基本面看点']
    video1 = res['video1']
    rank = res['行业排名']

    res_dict = {
        'fundTxt': fundTxt,
        'evaluate': evaluate,
        'capacity': capacity,
        'baseView': baseView,
        'video1': video1,
        'rank': jsonify(rank)
    }

    result = jsonify(res)

    return result, 200, {'mimetype': 'application/json'}

@all_info_bp.route('/hot_plate_data', methods = ["GET"])
def get_hot_plate_data():
    trade_date = request.args.get("date") or singleToday

    if (not trade_date):
        return 404

    df = pd.DataFrame()

    try:
        df = pd.read_csv(root_path + '/stock_analyse_tool_data_crawl/database/自研问句/%s/热门板块.csv' % trade_date)
    except Exception as e:
        print(e)

    jsonDf = df.to_json(orient="records", force_ascii=False)

    response = {
        'data': jsonDf,
        'code': 200,
        'msg': '成功'
    }
    return response, 200

