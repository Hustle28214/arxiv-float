import re
from urllib.parse import urlparse
from datetime import datetime, timedelta

def extract_arxiv_id_from_url(url):
    """从 arXiv URL 提取纯 ID（不含版本号）"""
    path = urlparse(url).path
    match = re.search(r'/(?:abs|pdf)/(\d{4}\.\d{4,5})(?:v\d+)?', path)
    if match:
        return match.group(1)
    # 兼容旧格式
    match = re.search(r'/(?:abs|pdf)/(.+?)(?:\.pdf)?$', path)
    if match:
        return match.group(1).split('v')[0]
    return None

def normalize_entry_id(entry_id):
    """规范化 Entry ID，返回纯 arXiv ID 作为缓存键"""
    arxiv_id = extract_arxiv_id_from_url(entry_id)
    return arxiv_id if arxiv_id else entry_id

def sanitize_filename(title):
    """将标题转换为安全的文件名"""
    return re.sub(r'[\\/*?:"<>|]', "", title).strip()[:100]

def get_date_range(period):
    """根据时间段返回开始日期字符串（用于 arXiv 查询）"""
    today = datetime.now()
    if period == "3年":
        start_date = today - timedelta(days=3*365)
    elif period == "2年":
        start_date = today - timedelta(days=2*365)
    elif period == "1年":
        start_date = today - timedelta(days=365)
    elif period == "6个月":
        start_date = today - timedelta(days=180)
    elif period == "3个月":
        start_date = today - timedelta(days=90)
    else:
        start_date = today - timedelta(days=365)
    return start_date.strftime("%Y%m%d") + "000000"

def open_url(url):
    """使用 Qt 桌面服务安全打开链接（需要 QApplication 环境，但作为工具函数保留）"""
    from PyQt6.QtGui import QDesktopServices
    from PyQt6.QtCore import QUrl
    if not url:
        return
    try:
        QDesktopServices.openUrl(QUrl(url))
    except Exception as e:
        print(f"打开链接失败: {e}")
