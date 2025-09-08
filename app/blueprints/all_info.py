import sys
import os

sys.path.append('/usr/src/stock_analyse_tool_back_end_flask')
from flask import Blueprint, request, Response, jsonify
from app.models.stock_data import StockData
import pandas as pd
import akshare as ak
import datetime
from config import root_path
import pywencai
from app.utils.index import requestForNew, clean_json, remove_field_from_objects, requestForQKA
import time
import requests
import json
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

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
        reqUrl = 'https://basic.10jqka.com.cn/basicapi/finance/stock/index/single/?code=%s&market=%s&id=parent_holder_net_profit&period=0&locale=zh_CN' % (
            stockCode, marketId)
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
        content = requestForQKA(reqUrl).json()

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
        roe_data_task = fetch_roe_data(session, stockCode, marketId)

        stock_data, stock_error = await stock_data_task
        financial_data, finance_error = await financial_data_task
        roe_data, roe_error = await roe_data_task

        return stock_data, stock_error, financial_data, finance_error, roe_data, roe_error


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
        stock_data, stock_error, financial_data, finance_error, roe_data, roe_error = loop.run_until_complete(
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

        if roe_error:
            errorInfo['roe_error'] = roe_error
            data['roe_data'] = []
        else:
            data['roe_data'] = roe_data['data']['data'][:9]

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

    content = requestForQKA('https://eq.10jqka.com.cn/plateTimeSharing/plateIndexData/%s.txt' % pid).json()

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


# 获取股票历史K线数据
@all_info_bp.route('/stock_history', methods=["GET"])
def get_stock_history():
    try:
        # 获取请求参数，设置默认值
        symbol = request.args.get("symbol") or ''
        period = request.args.get("period") or 'daily'
        start_date = request.args.get("start_date") or singleToday
        end_date = request.args.get("end_date") or singleToday
        adjust = request.args.get("adjust") or 'qfq'
        
        # 参数验证
        if not symbol:
            return {
                'data': None,
                'code': 400,
                'msg': '股票代码不能为空'
            }, 400
            
        # 调用akshare获取股票历史数据
        stock_hist_df = ak.stock_zh_a_hist(
            symbol=symbol,
            period=period,
            start_date=start_date,
            end_date=end_date,
            adjust=adjust
        )
        
        # 检查是否获取到数据
        if stock_hist_df.empty:
            return {
                'data': None,
                'code': 404,
                'msg': '未找到符合条件的数据'
            }, 200
            
        # 转换为JSON格式
        stock_hist_data = stock_hist_df.to_json(orient="records", force_ascii=False)
        
        # 返回成功响应
        return {
            'data': stock_hist_data,
            'code': 200,
            'msg': '成功'
        }, 200
        
    except Exception as e:
        # 异常处理
        return {
            'data': None,
            'code': 500,
            'msg': f'获取股票历史数据失败: {str(e)}'
        }, 200


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

@all_info_bp.route('/get_qka_data', methods=["GET"])
def get_plate_time_sharing_data():
    """
    获取指定板块的分时数据

    参数:
    plate_code -- 板块代码 (例如: 885427)
    max_retries -- 最大重试次数 (默认: 3)
    backoff_factor -- 重试等待时间因子 (默认: 0.5)

    返回:
    成功: 解析后的JSON数据
    失败: None (会打印错误信息)
    """
    url = request.args.get("url") or ''

    max_retries=3
    backoff_factor=0.5
    
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Host": "eq.10jqka.com.cn",
        "Accept": "text/plain, */*; q=0.01",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
        "Connection": "keep-alive",
        "X-Requested-With": "XMLHttpRequest",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-site"
    }

    # 创建带有重试机制的会话
    session = requests.Session()

    # 配置重试策略
    retry_strategy = Retry(
        total=max_retries,
        backoff_factor=backoff_factor,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["GET"]
    )

    # 创建适配器并挂载到会话
    adapter = HTTPAdapter(max_retries=retry_strategy)

    # 修正这里：使用 session.mount 而不是 session.mounts
    session.mount("https://", adapter)
    session.mount("http://", adapter)

    try:
        # 发送请求
        response = session.get(
            url,
            headers=headers,
            timeout=10
        )
        response.raise_for_status()  # 检查HTTP错误状态码
        # 处理响应内容
        content = response.text.strip()
        # 尝试解析JSON
        try:
            # 有些响应可能是JSONP格式，需要处理
            if content.startswith("/*") and content.endswith("*/"):
                content = content[2:-2].strip()

            # 尝试解析JSON
            return json.loads(content)
        except json.JSONDecodeError:
            # 如果解析失败，尝试提取可能的JSON部分
            if '{' in content and '}' in content:
                start = content.find('{')
                end = content.rfind('}') + 1
                try:
                    return json.loads(content[start:end])
                except json.JSONDecodeError:
                    pass

            print(f"JSON解析失败，原始响应: {content[:200]}...")
            return None

    except requests.exceptions.RequestException as e:
        print(f"请求失败: {e}")
        return None
    finally:
        session.close()  # 确保关闭会话


# 将服务器本地的每日日报返回给前端
@all_info_bp.route('/get_daily_report', methods=["GET"])
def get_daily_report():
    env_path = ''
    if sys.platform.startswith('darwin'):
        env_path = 'quant/'
    # 获取交易日期
    sh_index_file_path = f'{root_path}/{env_path}stock_data_base/data/指数历史日线数据/sh000001.csv'

    szzs = pd.read_csv(sh_index_file_path)

    # 最后一日交易日期
    trade_date = szzs.iloc[-1]['candle_end_time']

    # 倒数第二日交易日期，用于当日日报没数据时使用
    trade_date_prev = ''

    # 构建文件路径
    file_path = f'{root_path}/stock_analyse_tool_data_crawl/database/每日日报/{trade_date}/{trade_date}.md'
    try:
        # 检查文件是否存在
        if not os.path.exists(file_path):
            # 如果不存在，获取前一日的交易日期
            trade_date_prev = szzs.iloc[-2]['candle_end_time']
            file_path = f'{root_path}/stock_analyse_tool_data_crawl/database/每日日报/{trade_date_prev}/{trade_date_prev}.md'

            # 再次检查文件是否存在
            if not os.path.exists(file_path):
                return {
                    'data': {
                        'content': None,
                        'tradeDate': trade_date,
                        'tradeDatePrev': trade_date_prev
                    },
                    'code': 404,
                    'msg': '未获取到当日日报'
                }

        # 读取文件内容
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()

        return {
            'data': {
                'content': content,
                'tradeDate': trade_date,
                'tradeDatePrev': trade_date_prev
            },
            'code': 200,
            'msg': '成功'
        }

    except Exception as e:
        return {
            'data': {
                'content': None,
                'tradeDate': trade_date,
                'tradeDatePrev': trade_date_prev
            },
            'code': 500,
            'msg': f'获取当日日报失败: {str(e)}'
        }, 500


def get_latest_trade_date():
    """
    获取A股最新交易日期的函数
    返回格式: 字符串格式的日期 (YYYY-MM-DD)
    """
    try:
        # 获取上证指数日线数据
        df = ak.stock_zh_index_daily(symbol="sh000001")
        
        # 检查数据是否为空
        if df.empty:
            return None
            
        # 获取最后一条数据的日期（最新交易日）
        latest_date = df.iloc[-1]['date']
        
        # 转换为字符串格式
        return latest_date.strftime('%Y-%m-%d')
        
    except Exception as e:
        print(f"获取数据时出错: {e}")
        return None

def get_previous_nth_trade_day(n):
    """
    获取前第N个交易日的函数
    返回格式: 字符串格式的日期 (YYYY-MM-DD)
    """
    try:
        # 获取上证指数日线数据
        df = ak.stock_zh_index_daily(symbol="sh000001")
        
        # 检查数据是否为空
        if df.empty:
            return None
            
        # 检查n是否超出数据范围
        if n >= len(df):
            return None
            
        # 获取倒数第n+1条数据的日期（因为iloc[-1]是最后一条，iloc[-2]是倒数第二条，以此类推）
        previous_date = df.iloc[-(n+1)]['date']
        
        # 转换为字符串格式
        return previous_date.strftime('%Y-%m-%d')
        
    except Exception as e:
        print(f"获取数据时出错: {e}")
        return None


@all_info_bp.route('/latest_trade_date', methods=['GET'])
def latest_trade_date():
    """Flask接口：返回最新交易日期"""
    trade_date = get_latest_trade_date()
    
    if trade_date:
        return trade_date
    else:
        return '请求交易日期错误', 500


@all_info_bp.route('/previous_nth_trade_day', methods=['GET'])
def previous_nth_trade_day():
    """Flask接口：返回前第N个交易日"""
    try:
        n = request.args.get('n', type=int, default=1)
        
        if n <= 0:
            return jsonify({
                'error': '参数n必须大于0',
                'code': 400
            }), 400
            
        trade_date = get_previous_nth_trade_day(n)
        
        if trade_date:
            return jsonify({
                'data': trade_date,
                'code': 200,
                'msg': '成功'
            })
        else:
            return jsonify({
                'error': '获取交易日期失败或n超出数据范围',
                'code': 500
            }), 500
            
    except ValueError:
        return jsonify({
            'error': '参数n必须是整数',
            'code': 400
        }), 400
