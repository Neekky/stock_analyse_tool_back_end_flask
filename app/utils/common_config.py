import sys
# 根据不同的系统，设置不同的路径
prodPath = ''
if sys.platform.startswith('darwin'):
    prodPath = '/quant'