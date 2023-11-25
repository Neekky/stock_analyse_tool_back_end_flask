from flask import Flask, request, jsonify
from flask_cors import CORS
import pandas as pd

import akshare as ak
import datetime

singleToday = datetime.datetime.now().strftime("%Y%m%d")

app = Flask(__name__)
CORS(app)

@app.route('/')
def hello_world():  # put application's code here
    return 'Hello World!'

@app.route('/get_stock_k_line', methods = ["GET"])
def get_stock_k_line():  # put application's code here
    # 可以通过 request 的 args 属性来获取参数
    symbol = request.args.get("symbol") or ''

    if (not symbol):
        return 404

    period = request.args.get("period") or 'daily'
    start_date = request.args.get("start_date") or None
    adjust = request.args.get("adjust") or ''
    end_date = request.args.get("end_date")
    stock_zh_a_hist_df = ak.stock_zh_a_hist(symbol=symbol, period=period, start_date=start_date,
                                            adjust=adjust)
    response = stock_zh_a_hist_df.to_json(orient="records", force_ascii=False)
    return response

@app.route('/get_limitup_rank', methods = ["GET"])
def get_limitup_rank():

    start_date = request.args.get("start_date") or None

    if (not start_date):
        return '500'

    df = pd.read_csv('/Users/cengchao/studyDocument/stock_analyse_tool_data_crawl/database/每日涨停/%s/今日涨停.csv' % start_date)
    df['涨停封单额排名'] = df['涨停封单额[%s]' % start_date].rank(ascending=False, method='min')
    df['涨停开板次数排名'] = df['涨停开板次数[%s]' % start_date].rank(ascending=True, method='dense')
    df['最终涨停时间排名'] = df['最终涨停时间[%s]' % start_date].rank(ascending=True, method='dense')
    df['连续涨停天数排名'] = df['连续涨停天数[%s]' % start_date].rank(ascending=True, method='dense')
    df['a股市值排名'] = df['a股市值(不含限售股)[%s]' % start_date].rank(ascending=True, method='dense')

    df['复合因子'] = df['涨停封单额排名'] + df['涨停开板次数排名'] + df['最终涨停时间排名'] + df['连续涨停天数排名'] + df['a股市值排名']

    # 对因子进行排名
    df['排名'] = df['复合因子'].rank(method="first")
    # df = df[df['排名'] <= 5]
    response = df.to_json(orient="records", force_ascii=False)
    return response
if __name__ == '__main__':
    app.run()
