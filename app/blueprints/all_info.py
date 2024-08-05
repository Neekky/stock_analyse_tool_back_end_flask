import sys
sys.path.append('/usr/src/stock_analyse_tool_back_end_flask')
from flask import Blueprint, request, Response, jsonify
from app.models.stock_data import StockData
import pandas as pd
import akshare as ak
import datetime
from config import root_path
import pywencai
from app.utils.index import requestForNew, clean_json, remove_field_from_objects

singleToday = datetime.datetime.now().strftime("%Y%m%d")

all_info_bp = Blueprint('stock_info', __name__, url_prefix='/all_info')

@all_info_bp.route('/query_profit', methods = ["GET"])
def query_profit():
    stockCode = request.args.get("stockCode") or ''
    marketId = request.args.get("marketId") or '33'
    print(stockCode, marketId)
    if (not stockCode):
        return {
            'data': [],
            'code': 500,
            'msg': '未传stockCode'
        }
    reqUrl = 'https://basic.10jqka.com.cn/basicapi/finance/stock/index/single/?code=%s&market=%s&id=parent_holder_net_profit&period=0&locale=zh_CN' % (stockCode, marketId)

    content = requestForNew(reqUrl).json()
    if not content:
        response = {
            'data': [],
            'code': 500,
            'msg': '无数据'
        }
        return response

    response = {
        'data': content['data']['data'][:6],
        'code': 200,
        'msg': '成功'
    }

    return response, 200

# 问财通用查询
@all_info_bp.route('/querymoney', methods = ["GET"])
def wencai_stock_filter_universal_method():
    query = request.args.get("query") or ''

    if (not query):
        return 404

    page = 1
    # 首选方式问财
    res = pywencai.get(query=query, page=page)
    # 判断res是否为空
    if res is None:
        df = pd.DataFrame()  # Default DataFrame
    else:
        df = res

    # 当结果大于等于100或res的shape不存在，则页数+1，继续请求
    while True:
        if res is not None and (res.shape[0] >= 100):
            page += 1
            res = pywencai.get(query=query, page=page)
            df = pd.concat([df, res], ignore_index=True)
        else:
            break
    jsonDf = df.to_json(orient="records", force_ascii=False)

    # 处理数据
    cleaned_data = clean_json(jsonDf)

    cleaned_data = remove_field_from_objects(cleaned_data, '涨停明细数据')

    response = {
        'data': cleaned_data,
        'code': 200,
        'msg': '成功'
    }
    return response, 200

# 个股的基本面怎么样
@all_info_bp.route('/fundamentals', methods = ["GET"])
def get_stock_fundamentals():
    name = request.args.get("name") or ''

    if (not name):
        return 404
    query = '%s的基本面怎么样' % name

    # 首选方式问财
    res = pywencai.get(query=query)

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

# 获取热门板块的龙头股
@all_info_bp.route('/hot_plate_stock_data', methods = ["GET"])
def get_hot_plate_stock_data():
    pid = request.args.get("pid") or None

    if (not pid):
        return {
            'data': [],
            'code': 500,
            'msg': '未传递板块id'
        }

    content = requestForNew('https://eq.10jqka.com.cn/plateTimeSharing/plateIndexData/%s.txt' % pid).json()

    if not content:
        response = {
            'data': [],
            'code': 500,
            'msg': '无数据'
        }
        return response

    response = {
        'data': content,
        'code': 200,
        'msg': '成功'
    }

    return response, 200

@all_info_bp.route('/all_stock_list', methods = ["GET"])
def get_all_stock_list():
    stock_zh_a_spot_em_df = ak.stock_zh_a_spot_em()

    data = stock_zh_a_spot_em_df.to_json(orient="records", force_ascii=False)

    if (not data):
        return {
            'data': [],
            'code': 500,
            'msg': '无数据'
        }

    response = {
        'data': data,
        'code': 200,
        'msg': '成功'
    }
    return response


