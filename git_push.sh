#!/bin/bash

# 配置Git环境变量，如果需要的话
# export GIT_SSH_COMMAND='ssh -i /path/to/your/private_key'

/root/.pyenv/shims/python3 /usr/src/stock_analyse_tool_back_end_flask/update.py

# 定义仓库的本地目录
REPO_DIR="/usr/src/stock_analyse_tool_back_end_flask"

# 跳转到仓库目录
cd $REPO_DIR

# 检查并拉取最新的远程仓库变动
git pull

# 添加所有变动到暂存区
git add .

# 为变动创建一个提交
# 注意：这里使用了date命令来生成提交信息，你可以根据需要自定义
git commit -m "feat: 更新每日数据"

# 推送变动到远程仓库的主分支
# 你可能需要将'master'替换为你想要推送的实际分支名
git push origin master
