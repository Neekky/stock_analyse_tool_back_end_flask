import os
import pandas as pd
import akshare as ak
from datetime import datetime

# 定义数据存储路径
data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../database/other'))
trade_date_file = os.path.join(data_dir, 'a_share_trade_dates.csv')


def update_a_share_trade_dates():
    """
    更新A股交易日期数据
    
    逻辑：
    1. 检查本地是否存在交易日期数据
    2. 如果存在，读取数据并获取最后一条记录的年份
    3. 比较当前年份与最后一条记录的年份
    4. 如果当前年份大于最后一条记录的年份，调用akshare获取最新数据并更新
    5. 如果不存在，直接调用akshare获取数据并保存
    
    Returns:
        bool: 更新是否成功
    """
    try:
        # 确保数据目录存在
        os.makedirs(data_dir, exist_ok=True)
        
        # 获取当前年份
        current_year = datetime.now().year
        
        # 检查本地文件是否存在
        if os.path.exists(trade_date_file):
            # 读取本地数据
            df = pd.read_csv(trade_date_file)
            
            if not df.empty:
                # 获取最后一条记录的年份
                last_date = df['trade_date'].iloc[-1]
                last_year = pd.to_datetime(last_date).year
                
                # 比较年份
                if current_year > last_year:
                    # 获取最新数据
                    new_df = ak.tool_trade_date_hist_sina()
                    # 保存数据
                    new_df.to_csv(trade_date_file, index=False)
                    print(f"更新交易日期数据成功，从 {last_year} 年更新到 {current_year} 年")
                    return True
                else:
                    print("交易日期数据已是最新，无需更新")
                    return True
            else:
                # 数据为空，重新获取
                new_df = ak.tool_trade_date_hist_sina()
                new_df.to_csv(trade_date_file, index=False)
                print("交易日期数据为空，已重新获取")
                return True
        else:
            # 文件不存在，首次获取
            new_df = ak.tool_trade_date_hist_sina()
            new_df.to_csv(trade_date_file, index=False)
            print("首次获取交易日期数据成功")
            return True
    except Exception as e:
        print(f"更新交易日期数据失败: {e}")
        return False


def get_latest_trade_date():
    """
    获取最新的A股交易日期
    
    逻辑：
    1. 每次调用时都检查是否需要更新数据（基于年份）
    2. 检查本地是否存在交易日期数据
    3. 如果不存在或数据为空，调用update_a_share_trade_dates获取数据
    4. 读取本地数据，转换日期格式
    5. 过滤出小于或等于当前日期的日期
    6. 返回最新的日期
    
    Returns:
        str: 最新交易日期，格式为YYYY-MM-DD
    """
    try:
        # 每次调用都检查是否需要更新数据（基于年份）
        update_a_share_trade_dates()
        
        # 检查本地文件是否存在
        if not os.path.exists(trade_date_file) or os.path.getsize(trade_date_file) == 0:
            return None
        
        # 读取本地数据
        df = pd.read_csv(trade_date_file)
        
        if df.empty:
            return None
        
        # 转换日期格式
        df['trade_date'] = pd.to_datetime(df['trade_date'])
        
        # 获取当前日期
        current_date = datetime.now()
        
        # 过滤出小于或等于当前日期的日期
        valid_dates = df[df['trade_date'] <= current_date]
        
        if valid_dates.empty:
            return None
        
        # 返回最新的日期
        latest_date = valid_dates['trade_date'].iloc[-1]
        return latest_date.strftime('%Y-%m-%d')
    except Exception as e:
        print(f"获取最新交易日期失败: {e}")
        return None


if __name__ == "__main__":
    # 测试更新方法
    update_result = update_a_share_trade_dates()
    print(f"更新结果: {update_result}")
    
    # 测试获取最新交易日期方法
    latest_date = get_latest_trade_date()
    print(f"最新交易日期: {latest_date}")
