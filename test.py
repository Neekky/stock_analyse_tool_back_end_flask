import os

import akshare as ak
import pandas as pd
import pywencai

from app.utils.trend_analysis import batching_entry

# pd.set_option('display.max_rows', 3000)
pd.set_option('expand_frame_repr', False)  # 当列太多时不换行
# 设置命令行输出时的列对齐功能
pd.set_option('display.unicode.ambiguous_as_wide', True)
pd.set_option('display.unicode.east_asian_width', True)
pd.set_option('display.max_rows', None)  # 最多显示数据的行数
# stock_comment_detail_zlkp_jgcyd_em_df = ak.stock_comment_detail_zlkp_jgcyd_em(symbol="601162")
# print(stock_comment_detail_zlkp_jgcyd_em_df)
#
# stock_news_em_df = ak.stock_news_em(symbol="300644")
# print(stock_news_em_df)

# res = pywencai.get(query='闻泰科技股东减持', page=1)
# print(res['txt2'], '阿萨大大')
# df = pd.DataFrame(res['tableV1'])
# print(df, '阿萨大大')

# fund_etf_hist_em_df = ak.fund_etf_hist_em(symbol="513100", period="daily", end_date="20241012", adjust="qfq")
# print(fund_etf_hist_em_df)

# A 股股息率、A 股个股指标
# stock_add_stock_df = ak.stock_add_stock(stock="600004")
# print(stock_add_stock_df)

# stock_a_congestion_lg_df = ak.stock_a_congestion_lg()
# print(stock_a_congestion_lg_df)
# currency_boc_sina_df = ak.currency_boc_sina(symbol="美元", start_date="20231004", end_date="20241017")
# print(currency_boc_sina_df)
#
# currency_boc_safe_df = ak.currency_boc_safe()
# print(currency_boc_safe_df)


# currency_time_series_df = ak.currency_time_series(base="USD", start_date="2023-02-03", end_date="2024-10-31", symbols="CNY", api_key="1PT0QumQdGQOw6XFj9oBnUsFEjuTCGoH")
# print(currency_time_series_df)


stock_gdfx_free_holding_analyse_em_df = ak.stock_gdfx_free_holding_analyse_em(date="20241107")
print(stock_gdfx_free_holding_analyse_em_df)

# stock_gpzy_pledge_ratio_detail_em_df = ak.stock_gpzy_pledge_ratio_detail_em()
# print(stock_gpzy_pledge_ratio_detail_em_df)