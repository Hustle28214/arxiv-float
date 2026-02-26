# arxiv_float/workers/explanation.py
import re
import fitz
from PyQt6.QtCore import QThread, pyqtSignal
from ..utils.constants import create_ollama_client, MODEL_NAME

class ExplanationWorker(QThread):
    finished = pyqtSignal(list)
    error = pyqtSignal(str)

    def __init__(self, pdf_path, title, url, parent=None):
        super().__init__(parent)
        self.pdf_path = pdf_path
        self.title = title
        self.url = url

    def run(self):
        try:
            doc = fitz.open(self.pdf_path)
            full_text = ""
            for page_num in range(len(doc)):
                if self.isInterruptionRequested():
                    doc.close()
                    return
                page = doc.load_page(page_num)
                full_text += page.get_text()
            doc.close()

            patterns = [
                (r'(?i)\b(introduction|intro)\b', '引言'),
                (r'(?i)\b(related work|background)\b', '相关工作'),
                (r'(?i)\b(method|methodology|approach)\b', '方法'),
                (r'(?i)\b(experiment|evaluation|results)\b', '实验与结果'),
                (r'(?i)\b(discussion)\b', '讨论'),
                (r'(?i)\b(conclusion|conclusions|summary)\b', '结论')
            ]

            explanations = []
            client = create_ollama_client()
            for pattern, section_name in patterns:
                if self.isInterruptionRequested():
                    return
                match = re.search(pattern, full_text, re.IGNORECASE)
                if match:
                    start = max(0, match.start() - 500)
                    end = min(len(full_text), match.start() + 2000)
                    chunk = full_text[start:end]
                    prompt = f"你是一个科研助手。以下是一篇题为《{self.title}》的论文中关于“{section_name}”部分的文本片段，请用一段话（50-100字）详细解释该部分的核心内容、创新点或关键结论：\n\n{chunk[:1500]}"
                    try:
                        resp = client.chat(model=MODEL_NAME, messages=[{'role': 'user', 'content': prompt}])
                        summary = resp['message']['content']
                    except Exception as e:
                        summary = f"（AI摘要生成失败：{str(e)}）"
                    explanations.append((section_name, summary))

            if not explanations:
                explanations.append(("全文概述", "未能识别章节，请手动阅读原文。"))

            self.finished.emit(explanations)
        except Exception as e:
            self.error.emit(str(e))