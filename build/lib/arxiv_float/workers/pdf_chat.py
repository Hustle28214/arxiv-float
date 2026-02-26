import fitz
from PyQt6.QtCore import QThread, pyqtSignal
from ..utils.constants import create_ollama_client, MODEL_NAME

# 尝试导入 BM25
try:
    from rank_bm25 import BM25Okapi
    BM25_AVAILABLE = True
except ImportError:
    BM25_AVAILABLE = False

class PdfChatWorker(QThread):
    finished = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, pdf_path, question, paragraphs, bm25, parent=None):
        super().__init__(parent)
        self.pdf_path = pdf_path
        self.question = question
        self.paragraphs = paragraphs
        self.bm25 = bm25

    def run(self):
        try:
            # 检索最相关的段落（取前3个）
            if self.bm25 and self.paragraphs:
                tokenized_question = self.question.split()
                scores = self.bm25.get_scores(tokenized_question)
                # 获取前3个段落的索引
                top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:3]
                best_paras = [self.paragraphs[i] for i in top_indices if scores[i] > 0]
            elif self.paragraphs:
                # 简单关键词匹配
                words = set(self.question.lower().split())
                scored_paras = [(p, sum(1 for w in words if w in p.lower())) for p in self.paragraphs]
                scored_paras.sort(key=lambda x: x[1], reverse=True)
                best_paras = [p for p, score in scored_paras[:3] if score > 0]
            else:
                best_paras = []

            # 如果没有检索到，则使用全文开头
            if not best_paras:
                doc = fitz.open(self.pdf_path)
                full_text = ""
                for page in doc:
                    full_text += page.get_text()
                doc.close()
                best_paras = [full_text[:2000]]  # 取前2000字符

            context = "\n\n".join(best_paras)

            client = create_ollama_client()
            prompt = f"以下是一篇论文的相关段落，请根据这些段落内容回答用户的问题。\n\n段落：{context}\n\n问题：{self.question}\n\n请用中文详细回答。"
            resp = client.chat(model=MODEL_NAME, messages=[{'role': 'user', 'content': prompt}])
            answer = resp['message']['content']
            self.finished.emit(answer)
        except Exception as e:
            self.error.emit(str(e))
