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
import time

import asyncio
import aiohttp

singleToday = datetime.datetime.now().strftime("%Y%m%d")

all_info_bp = Blueprint('stock_info', __name__, url_prefix='/all_info')

def query_profit_backup():
    try:
        stockCode = request.args.get("stock_code") or ''
        marketId = request.args.get("market_id") or '33'
        start_date = request.args.get("start_date") or singleToday
        end_date = request.args.get("end_date") or singleToday
        period = request.args.get("period") or 'daily'
        adjust = request.args.get("adjust") or 'qfq'

        # 请求K线数据
        stock_zh_a_hist_df = ak.stock_zh_a_hist(
            symbol=stockCode,
            period=period,
            start_date=start_date,
            end_date=end_date,
            adjust=adjust
        )
        stock_zh_a_hist_data = stock_zh_a_hist_df.to_json(orient="records", force_ascii=False)

        if (not stockCode):
            return {
                'data': [],
                'code': 500,
                'msg': '未传stockCode'
            }

        # 请求财务数据
        reqUrl = 'https://basic.10jqka.com.cn/basicapi/finance/stock/index/single/?code=%s&market=%s&id=parent_holder_net_profit&period=0&locale=zh_CN' % (stockCode, marketId)
        content = requestForNew(reqUrl).json()

        if not content:
            response = {
                'data': {
                    'stock_intraday_em_data': [],
                    'query_profit': []
                },
                'code': 500,
                'msg': '无数据'
            }
            return response, 500

        response = {
            'data': {
                'stock_intraday_em_data': stock_zh_a_hist_data,
                'query_profit': content['data']['data'][:8]
            },
            'code': 200,
            'msg': '成功'
        }

        return response, 200

    except Exception as e:
        response = {
            'data': {
                'stock_intraday_em_data': [],
                'query_profit': []
            },
            'code': 500,
            'msg': f'发生异常: {str(e)}'
        }
        return response, 500

async def fetch_stock_data(session, stockCode, period, start_date, end_date, adjust):
    try:
        stock_zh_a_hist_df = ak.stock_zh_a_hist(
            symbol=stockCode,
            period=period,
            start_date=start_date,
            end_date=end_date,
            adjust=adjust
        )
        return stock_zh_a_hist_df.to_json(orient="records", force_ascii=False), None
    except Exception as e:
        return None, f"Fetching stock data failed: {str(e)}"


async def fetch_financial_data(session, stockCode, marketId):
    try:
        reqUrl = f'https://basic.10jqka.com.cn/basicapi/finance/stock/index/single/?code={stockCode}&market={marketId}&id=parent_holder_net_profit&period=0&locale=zh_CN'
        content = requestForNew(reqUrl).json()

        if not content:
            return None, '接口获取成功，没有内容'

        if content['status_msg'] != 'success':
            return None, '接口获取成功，后端报错%s' % content['status_msg']

        return content, None
    except Exception as e:
        return None, f"Fetching financial data failed: {str(e)}"

async def fetch_roe_data(session, stockCode, marketId):
    try:
        reqUrl = f'https://basic.10jqka.com.cn/basicapi/finance/stock/index/single/?code={stockCode}&market={marketId}&id=index_weighted_avg_roe&period=0&locale=zh_CN'
        content = requestForNew(reqUrl).json()

        if not content:
            return None, '接口获取成功，没有内容'

        if content['status_msg'] != 'success':
            return None, '接口获取成功，后端报错%s' % content['status_msg']

        return content, None
    except Exception as e:
        return None, f"Fetching financial data failed: {str(e)}"


async def fetch_all_data(stockCode, marketId, start_date, end_date, period, adjust):
    async with aiohttp.ClientSession() as session:
        stock_data_task = fetch_stock_data(session, stockCode, period, start_date, end_date, adjust)
        financial_data_task = fetch_financial_data(session, stockCode, marketId)
        # roe_data_task = fetch_roe_data(session, stockCode, marketId)

        stock_data, stock_error = await stock_data_task
        financial_data, finance_error = await financial_data_task
        # roe_data, roe_error = await roe_data_task

        return stock_data, stock_error, financial_data, finance_error

@all_info_bp.route('/query_profit', methods=["GET"])
def query_profit():
    try:
        stockCode = request.args.get("stock_code") or ''
        marketId = request.args.get("market_id") or '33'
        start_date = request.args.get("start_date") or singleToday
        end_date = request.args.get("end_date") or singleToday
        period = request.args.get("period") or 'daily'
        adjust = request.args.get("adjust") or 'qfq'

        if not stockCode:
            return {
                'data': [],
                'code': 500,
                'msg': '未传stockCode'
            }

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)

        # 这里请求了股票K线、股票的归母净利润数据、ROE数据
        stock_data, stock_error, financial_data, finance_error = loop.run_until_complete(
            fetch_all_data(stockCode, marketId, start_date, end_date, period, adjust)
        )

        errorInfo = {}
        data = {}

        if stock_error:
            errorInfo['stock_error'] = stock_error
            data['stock_intraday_em_data'] = []
        else:
            data['stock_intraday_em_data'] = stock_data


        if finance_error:
            errorInfo['finance_error'] = finance_error
            data['query_profit'] = []
        else:
            data['query_profit'] = financial_data['data']['data'][:9]

        # if roe_error:
        #     errorInfo['roe_error'] = roe_error
        #     data['roe_data'] = []
        # else:
        #     data['roe_data'] = roe_data['data']['data'][:9]

        response = {
            'data': data,
            'code': 200,
            'msg': errorInfo
        }
        return response, 200

    except Exception as e:
        return {
            'data': {
                'stock_intraday_em_data': [],
                'query_profit': [],
                # 'roe_data': []
            },
            'code': 500,
            'msg': f'发生异常: {str(e)}'
        }, 500


# 问财通用查询-股票列表
@all_info_bp.route('/querymoney', methods=["GET"])
def wencai_stock_filter_universal_method():
    query = request.args.get("query") or ''

    if (not query):
        return 404
    df = pd.DataFrame()

    max_retries = 3
    wait_time = 2

    page = 1
    retries = 0

    while retries < max_retries:
        try:
            # 首选方式问财
            res = pywencai.get(query=query, page=page, sort_order='asc')

            # 判断res是否为空
            if res is None:
                res = pd.DataFrame()  # Default DataFrame

            # 合并数据
            df = pd.concat([df, res], ignore_index=True)

            # 当结果大于等于100，则页数+1，继续请求
            if res.shape[0] >= 100:
                page += 1
                continue
            else:
                break  # 没有更多数据，退出循环

        except Exception as e:
            retries += 1
            print(f"Error occurred: {e}. Retrying {retries}/{max_retries}...")
            time.sleep(wait_time)  # 等待一段时间后重试

            if retries >= max_retries:
                print("Max retries reached. Exiting.")
                return None  # 返回 None 或者其他指示失败的值

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

# 问财通用查询-个股信息
@all_info_bp.route('/querymoney_info', methods=["GET"])
def wencai_stock_info():
    query = request.args.get("query") or ''

    if (not query):
        return 404

    max_retries = 3
    wait_time = 2

    retries = 0

    res = {}

    while retries < max_retries:
        try:
            # 首选方式问财
            res = pywencai.get(query=query, page=1, sort_order='asc')

            # 判断res是否为空
            if res is None:
                res = {}  # Default DataFrame

            print(res)
            if res['txt2'] is None:
                desc = ''
            else:
                desc = res['txt2']

            res = {
                'desc': desc,
            }
            break

        except Exception as e:
            retries += 1
            print(f"Error occurred: {e}. Retrying {retries}/{max_retries}...")
            time.sleep(wait_time)  # 等待一段时间后重试

            if retries >= max_retries:
                print("Max retries reached. Exiting.")
                return None  # 返回 None 或者其他指示失败的值

    response = {
        'data': res,
        'code': 200,
        'msg': '成功'
    }
    return response, 200

# 个股的基本面怎么样
@all_info_bp.route('/fundamentals', methods=["GET"])
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


@all_info_bp.route('/hot_plate_data', methods=["GET"])
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
@all_info_bp.route('/hot_plate_stock_data', methods=["GET"])
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


@all_info_bp.route('/all_stock_list', methods=["GET"])
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

# 获取指数日线数据, 默认获取上证指数
@all_info_bp.route('/stock_zh_index_daily', methods=["GET"])
def get_stock_zh_index_daily():
    symbol = request.args.get("symbol") or 'sh000001'

    stock_zh_a_spot_em_df = ak.stock_zh_index_daily_em(symbol=symbol)

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


@all_info_bp.route('/get_trade_date', methods=["GET"])
def get_trade_date():
    try:
        content = requestForNew('https://hq.sinajs.cn/list=sh000001').text
        data_date = str(content.split(',')[-4])

        response = {
            'data': data_date,
            'code': 200,
            'msg': '成功'
        }
        return response

    except Exception as e:
        # 捕获其他异常并返回错误信息
        return {
            'data': None,
            'code': 500,
            'msg': f'发生异常: {str(e)}'
        }

# 使用akshare请求股债利差数据
@all_info_bp.route('/get_stock_ebs_lg', methods=["GET"])
def get_stock_ebs_lg():
    try:
        content = ak.stock_ebs_lg()
        
        if content is None or content.empty:
            return {
                'data': None,
                'code': 404,
                'msg': '未获取到股债利差数据'
            }, 404

        data = content.to_json(orient="records", force_ascii=False)
        
        return {
            'data': data,
            'code': 200,
            'msg': '成功'
        }, 200

    except Exception as e:
        return {
            'data': None,
            'code': 500,
            'msg': f'获取股债利差数据失败: {str(e)}'
        }, 500