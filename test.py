import akshare as ak
import pandas as pd

pd.set_option('display.max_rows', 1000)
pd.set_option('expand_frame_repr', False)  # 当列太多时不换行
# 设置命令行输出时的列对齐功能
pd.set_option('display.unicode.ambiguous_as_wide', True)
pd.set_option('display.unicode.east_asian_width', True)

stock_zh_a_hist_df = ak.stock_zh_a_hist(symbol='600712', period='daily', start_date='20230612',
                                            adjust='')
print(stock_zh_a_hist_df)