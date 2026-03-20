# CLAUDE.md

本文档为 Claude Code (claude.ai/code) 提供操作本代码库的指导。

## 项目概述

这是一个基于 Flask 的股票分析工具后端 API，提供 A 股、港股和美股的数据接口。应用从并行的数据爬取项目中读取预处理的 CSV 数据文件，同时也会实时调用外部数据源（akshare、tushare、雪球）。

## 运行应用

```bash
# 安装依赖
pip install -r requirements.txt

# 本地运行
python run.py

# 生产环境运行 (gunicorn)
gunicorn -w 4 run:flask_app
```

应用需要设置 `TUSHARE_TOKEN` 环境变量以使用 tushare API。

## 关键配置

- `config.py`：定义 `root_path`（项目根目录的父目录）和 `SQLALCHEMY_DATABASE_URI`
- `app/utils/common_config.py`：定义 `prodPath` —— macOS 上为 `/quant`，Linux 上为空。用于构建指数 CSV 数据文件的路径
- `run.py` 会将 `/usr/src/stock_analyse_tool_back_end_flask` 添加到 `sys.path` 以适配生产环境 Linux 部署；本地开发依赖相对导入

## 架构

### 应用工厂 (`app/__init__.py`)
创建 Flask 应用，配置 CORS（允许的源：localhost:8100 和 mfuture.fun），注册蓝图。SQLAlchemy 数据库已初始化但目前被注释掉 —— 模型存在但未实际使用。

### 蓝图 (`app/blueprints/`)
| 蓝图 | URL 前缀 | 职责 |
|---|---|---|
| `main` | `/` | 健康检查 |
| `stock_data` | (根路径) | 股票/指数 K 线、见顶见底概率、涨停数据 |
| `all_info` | `/all_info` | 综合股票信息、收益查询、异步数据 |
| `stock_selection_model` | `/stock_selection_model` | KDJ 选股模型 |

### 数据源
项目中混合使用两种数据访问方式：
1. **文件读取**：从并行项目 `root_path + '/stock_analyse_tool_data_crawl/database/...'` 读取 CSV 文件。该并行项目必须与本项目并存。
2. **实时 API**：akshare (`ak.*`)、tushare (`ts.pro_api()`)、雪球（通过 `data_crawl.large_model.crawler_func.get_xueqiu_index`）。雪球模块通过 `sys.path.append` 从并行数据爬取项目导入。

### 每日更新脚本 (`update.py`)
独立运行（非 Flask 调用），重新计算指数见顶见底概率 CSV 并保存到 `database/other/`。由 cron 或交易日在交易日手动调用。通过 `getDate()` 查询新浪财经确认当天是否为交易日。

### 本地数据库 (`database/other/`)
API 服务的预计算 CSV 文件：
- `index_top_bottom_percent.csv` —— A股（上证指数）见顶见底信号
- `hk_hsi_top_bottom_percent.csv` —— 恒生指数信号
- `us_dji_top_bottom_percent.csv` —— 道琼斯信号
- `a_share_trade_dates.csv` —— A股交易日历，每年通过 `app/utils/update_trade.py` 自动更新

### 工具模块 (`app/utils/`)
- `index.py`：HTTP 辅助函数（`requestForNew`、`requestForQKA`）、日期工具（`getDate` 查询新浪财经获取最新交易日）、JSON 键清理
- `trend_analysis.py`：指数 DataFrame 的技术分析 —— EMA、MA、趋势方向、见顶见底概率（`batching_entry`）
- `hk_hsi_trend_analysis.py`：适配港股恒指数据格式的相同逻辑
- `update_trade.py`：通过 akshare 管理 `a_share_trade_dates.csv`，年份变更时自动刷新
- `common_config.py`：平台相关的路径前缀

## 外部依赖
- **akshare**：主要市场数据源（免费）
- **tushare**：次要数据源（需要通过 `TUSHARE_TOKEN` 环境变量设置 token）
- **雪球**：用于指数 K 线数据；需要在项目根目录放置 `xueqiu_cookies.json` cookie 文件
- **并行项目** `stock_analyse_tool_data_crawl`：必须存在于 `root_path + '/stock_analyse_tool_data_crawl'`；提供爬虫函数和预构建的 CSV 数据库

## 部署
通过 `.github/workflows/deploy-flask-app.yml` 进行 CI/CD —— 通过 SCP 将文件复制到服务器，然后执行 `systemctl restart flaskapp.service`。目前仅在 `cancle` 分支触发（非标准分支名，有意为之）。需要以下 Secrets：`SERVER_IP`、`SERVER_USER`、`SERVER_PASSWORD`、`SERVER_PORT`、`DEPLOY_PATH`。

## 编码规范

### 命名规范
- **变量/函数**：小写 + 下划线（`snake_case`），如 `get_stock_data`
- **类名**：首字母大写驼峰（`PascalCase`），如 `StockData`
- **常量**：全大写 + 下划线，如 `MAX_RETRY_COUNT`
- **私有成员**：单下划线前缀，如 `_internal_helper`
- **蓝图**：以 `_bp` 结尾，如 `stock_data_bp`

### 代码格式
- 使用 **4 空格** 缩进
- 行长度限制 **88 字符**（Black 默认）
- 字符串优先使用 **双引号**

### 导入排序
```python
# 1. 标准库
import os
import sys
from datetime import datetime

# 2. 第三方库
import pandas as pd
from flask import Blueprint, request

# 3. 本地应用导入
from app.utils.index import getDate
from config import root_path
```

### 日志使用
- 使用 Flask 的 `current_app.logger`，避免裸 `print`
- 日志级别：DEBUG（开发）、INFO（正常流程）、WARNING（可恢复问题）、ERROR（需要处理）
- 关键操作记录上下文：用户、股票代码、请求参数

### 文档字符串
- 使用 Google Style Docstring
```python
def get_stock_k_line(symbol: str, start_date: str = "") -> dict:
    """获取股票 K 线数据。

    Args:
        symbol: 股票代码，如 "000001"
        start_date: 开始日期，格式 "YYYYMMDD"，为空则取全部

    Returns:
        包含 code/data/msg 的字典

    Raises:
        ValueError: 参数校验失败时抛出
    """
```

### API 响应格式
统一响应结构：
```python
{
    "code": 200,      # HTTP 风格状态码
    "data": {},       # 成功时返回数据
    "msg": "请求成功"   # 提示信息
}
```

### 类型注解
- 函数参数和返回值使用类型注解
```python
from typing import Optional, List, Dict, Any

def analyze_trend(df: pd.DataFrame) -> tuple[int, int]:
    ...
```

