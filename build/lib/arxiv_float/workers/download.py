import os
import requests
from PyQt6.QtCore import QThread, pyqtSignal
from ..utils.helpers import sanitize_filename
from ..utils.constants import PDF_SAVE_DIR

class PdfDownloadWorker(QThread):
    finished = pyqtSignal(bool, str, str, bool)  # success, path, error, already_exists

    def __init__(self, arxiv_id, title, parent=None):
        super().__init__(parent)
        self.arxiv_id = arxiv_id
        self.title = title

    def run(self):
        try:
            pdf_url = f"https://arxiv.org/pdf/{self.arxiv_id}.pdf"
            filename = sanitize_filename(self.title) + ".pdf"
            save_path = os.path.join(PDF_SAVE_DIR, filename)
            if os.path.exists(save_path):
                self.finished.emit(True, save_path, "", True)
                return

            response = requests.get(pdf_url, stream=True)
            response.raise_for_status()
            with open(save_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            self.finished.emit(True, save_path, "", False)
        except Exception as e:
            self.finished.emit(False, "", str(e), False)
