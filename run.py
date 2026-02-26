#!/usr/bin/env python3
# run.py
import os
# 清除代理环境（必须在任何可能使用代理的库导入前执行）
for key in ['http_proxy', 'https_proxy', 'all_proxy', 'HTTP_PROXY', 'HTTPS_PROXY', 'ALL_PROXY']:
    os.environ.pop(key, None)
os.environ['NO_PROXY'] = '127.0.0.1,localhost'

import sys
from arxiv_float.app import main

if __name__ == "__main__":
    sys.exit(main())
