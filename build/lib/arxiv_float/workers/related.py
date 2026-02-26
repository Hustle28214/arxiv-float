import re
import fitz
import arxiv
from PyQt6.QtCore import QThread, pyqtSignal
from ..utils.constants import create_ollama_client, MODEL_NAME

class RelatedPapersWorker(QThread):
    finished = pyqtSignal(list)
    error = pyqtSignal(str)

    def __init__(self, pdf_path, title, parent=None):
        super().__init__(parent)
        self.pdf_path = pdf_path
        self.title = title

    def run(self):
        try:
            doc = fitz.open(self.pdf_path)
            full_text = ""
            for page in doc:
                full_text += page.get_text()
            doc.close()

            ref_patterns = [
                r'(?i)\b(References|Bibliography)\s*\n(.*?)(?=\n\s*\n\s*[A-Z]|\Z)',
                r'(?i)\b(REFERENCES)\s*\n(.*?)(?=\n\s*\n\s*[A-Z]|\Z)'
            ]
            ref_text = ""
            for pattern in ref_patterns:
                match = re.search(pattern, full_text, re.DOTALL)
                if match:
                    ref_text = match.group(2)
                    break

            if not ref_text:
                ref_text = full_text[-5000:]

            arxiv_ids = re.findall(r'arXiv:(\d{4}\.\d{4,5}(?:v\d+)?)', ref_text)
            if not arxiv_ids:
                arxiv_ids = re.findall(r'arxiv\.org/(?:abs|pdf)/(\d{4}\.\d{4,5}(?:v\d+)?)', ref_text)

            arxiv_ids = list(set(arxiv_ids))[:20]

            papers_info = []
            client = create_ollama_client()

            for idx in arxiv_ids:
                try:
                    search = arxiv.Search(id_list=[idx])
                    result = next(arxiv.Client().results(search))
                    title = result.title
                    summary = result.summary
                    url = result.entry_id
                    prompt = f"请判断以下论文与《{self.title}》的相关性（高/中/低），并用一句话说明理由：\n标题：{title}\n摘要：{summary[:500]}"
                    resp = client.chat(model=MODEL_NAME, messages=[{'role': 'user', 'content': prompt}])
                    reason = resp['message']['content']
                    papers_info.append({
                        'title': title,
                        'url': url,
                        'reason': reason
                    })
                except Exception:
                    continue
                if len(papers_info) >= 10:
                    break

            self.finished.emit(papers_info)
        except Exception as e:
            self.error.emit(str(e))
