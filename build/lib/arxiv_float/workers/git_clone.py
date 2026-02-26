import os
import subprocess
from PyQt6.QtCore import QThread, pyqtSignal

class GitCloneWorker(QThread):
    finished = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, repo_url, target_dir, parent=None):
        super().__init__(parent)
        self.repo_url = repo_url
        self.target_dir = target_dir

    def run(self):
        try:
            os.makedirs(self.target_dir, exist_ok=True)
            cmd = ['git', 'clone', self.repo_url, self.target_dir]
            process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
            stdout, stderr = process.communicate(timeout=300)  # 5分钟超时
            if process.returncode == 0:
                self.finished.emit(self.target_dir)
            else:
                self.error.emit(f"克隆失败: {stderr}")
        except subprocess.TimeoutExpired:
            process.kill()
            self.error.emit("克隆超时（超过5分钟）")
        except Exception as e:
            self.error.emit(str(e))
