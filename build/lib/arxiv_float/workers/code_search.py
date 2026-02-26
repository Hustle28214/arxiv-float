import requests
from PyQt6.QtCore import QThread, pyqtSignal

class CodeSearchWorker(QThread):
    finished = pyqtSignal(dict)
    error = pyqtSignal(str)

    def __init__(self, arxiv_id, parent=None):
        super().__init__(parent)
        self.arxiv_id = arxiv_id

    def run(self):
        try:
            url = f"https://paperswithcode.com/api/v1/papers/?arxiv_id={self.arxiv_id}"
            resp = requests.get(url, timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                if data['count'] > 0:
                    paper = data['results'][0]
                    repo_url = paper.get('repository_url')
                    if repo_url:
                        self.finished.emit({'repository_url': repo_url})
                    else:
                        self.error.emit("该论文没有关联的代码仓库。")
                else:
                    self.error.emit("未找到该论文在 Papers with Code 中的信息。")
            else:
                self.error.emit(f"API 请求失败: HTTP {resp.status_code}")
        except Exception as e:
            self.error.emit(str(e))
