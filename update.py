import sys
import pandas as pd
import os


sys.path.append('/usr/src/stock_analyse_tool_back_end_flask')
import datetime

from app.utils.index import getDate, singleToday
from app.utils.trend_analysis import batching_entry

tradeDate = getDate()
# 如果今天不是交易日，那么就结束代码执行
if (tradeDate != singleToday):
    exit()

# 获取当前脚本的目录
current_dir = os.path.dirname(os.path.abspath(__file__))

singleToday = datetime.datetime.now().strftime("%Y%m%d")

resdf = batching_entry('index', 'sh000001', '2018-01-01', singleToday)

# ===获取项目根目录
_ = os.path.abspath(os.path.dirname(__file__))  # 返回当前文件路径

# 定义数据存储路径
database_root_path = os.path.abspath(os.path.join(_, './database/other'))

# 校验 resdf 是否是一个有效的 DataFrame 且有数据
if isinstance(resdf, pd.DataFrame) and not resdf.empty:
    # 导出为 CSV 文件
    resdf.to_csv(database_root_path + '/index_top_bottom_percent.csv', index=False)
    print("DataFrame 已成功导出 index_top_bottom_percent.csv 指数见顶见底数据文件")
else:
    print("DataFrame 无效或没有数据，不进行导出。")
