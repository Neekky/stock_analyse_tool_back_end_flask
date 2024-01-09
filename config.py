import os

# ===获取项目根目录
_ = os.path.abspath(os.path.dirname(__file__))  # 返回当前文件路径

root_path = os.path.abspath(os.path.join(_, '../'))  # 返回根目录文件夹

SQLALCHEMY_DATABASE_URI = 'mysql://username:password@server/db'
SQLALCHEMY_TRACK_MODIFICATIONS = False
