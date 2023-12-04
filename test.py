import akshare as ak
import pandas as pd

pd.set_option('display.max_rows', 1000)
pd.set_option('expand_frame_repr', False)  # 当列太多时不换行
# 设置命令行输出时的列对齐功能
pd.set_option('display.unicode.ambiguous_as_wide', True)
pd.set_option('display.unicode.east_asian_width', True)

stock_lhb_detail_em_df = ak.stock_lhb_detail_em(start_date="20231130", end_date="20231130")
df_combined = stock_lhb_detail_em_df.groupby('代码').agg({
    '名称': 'first',
    '上榜日':  'first',
    '解读':  'first',
    '收盘价': 'first',
    '涨跌幅': 'first',
    '龙虎榜净买额': 'first',
    '龙虎榜买入额': 'first',
    '龙虎榜卖出额': 'first',
    '龙虎榜成交额': 'first',
    '市场总成交额': 'first',
    '净买额占总成交比': 'first',
    '成交额占总成交比': 'first',
    '换手率': 'first',
    '流通市值': 'first',
    '上榜原因': list,
    '上榜后1日': 'first',
    '上榜后2日': 'first',
    '上榜后5日': 'first',
    '上榜后10日': 'first',
}).reset_index()
print(df_combined)