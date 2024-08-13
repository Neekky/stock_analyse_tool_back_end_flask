import akshare as ak
import pandas as pd

pd.set_option('display.max_rows', 3000)
pd.set_option('expand_frame_repr', False)  # 当列太多时不换行
# 设置命令行输出时的列对齐功能
pd.set_option('display.unicode.ambiguous_as_wide', True)
pd.set_option('display.unicode.east_asian_width', True)

# fund_info_index_em_df = ak.fund_info_index_em(symbol="行业主题", indicator="全部")
# print(fund_info_index_em_df)
# fund_info_index_em_df.to_csv('111.csv')

fund_etf_spot_em_df = ak.fund_etf_spot_em()
print(fund_etf_spot_em_df)