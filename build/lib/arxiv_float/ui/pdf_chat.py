import os
import fitz
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QFrame, QHBoxLayout, QPushButton, QTextEdit, QLineEdit
from PyQt6.QtCore import Qt, pyqtSignal, QThread
from PyQt6.QtGui import QCursor
from ..utils.constants import MODEL_NAME, OLLAMA_HOST
from ..utils.helpers import open_url  # 虽然未使用，但保留导入

try:
    from rank_bm25 import BM25Okapi
    BM25_AVAILABLE = True
except ImportError:
    BM25_AVAILABLE = False

from ollama import Client

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
            # 检索最相关的多个段落
            if self.bm25 and self.paragraphs:
                tokenized_question = self.question.split()
                scores = self.bm25.get_scores(tokenized_question)
                # 获取前3个最高得分的索引
                top_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)[:3]
                best_paras = [self.paragraphs[i] for i in top_indices if scores[i] > 0]
            else:
                best_paras = self.paragraphs[:3] if self.paragraphs else []

            if not best_paras:
                # 如果检索不到，取全文开头
                doc = fitz.open(self.pdf_path)
                full_text = ""
                for page in doc:
                    full_text += page.get_text()
                doc.close()
                best_paras = [full_text[:2000]]

            context = "\n\n".join(best_paras)

            client = Client(host=OLLAMA_HOST)
            prompt = f"以下是一篇论文的相关段落，请根据这些段落内容回答用户的问题。\n\n段落：{context}\n\n问题：{self.question}\n\n请用中文详细回答。"

            from ..workers.global_ollama_lock import ollama_lock  # 需要全局锁，稍后定义
            ollama_lock.lock()
            resp = client.chat(model=MODEL_NAME, messages=[{'role': 'user', 'content': prompt}])
            answer = resp['message']['content']
            ollama_lock.unlock()
            self.finished.emit(answer)
        except Exception as e:
            self.error.emit(str(e))


class PdfChatWindow(QWidget):
    def __init__(self, pdf_path, title, parent=None):
        super().__init__(parent)
        self.pdf_path = pdf_path
        self.title = title
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_InputMethodEnabled, True)  # 启用输入法
        self.setFixedSize(500, 600)

        self.paragraphs = self.extract_paragraphs()
        if BM25_AVAILABLE and self.paragraphs:
            tokenized_paras = [para.split() for para in self.paragraphs]
            self.bm25 = BM25Okapi(tokenized_paras)
        else:
            self.bm25 = None

        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(15, 15, 15, 15)
        bg_frame = QFrame()
        bg_frame.setStyleSheet("""
            QFrame {
                background-color: rgba(35, 35, 35, 240);
                border-radius: 15px;
                border: none;
            }
        """)
        frame_layout = QVBoxLayout(bg_frame)
        frame_layout.setContentsMargins(15, 15, 15, 15)

        title_row = QHBoxLayout()
        title_label = QLabel(f"💬 与 PDF 对话: {title[:30]}...")
        title_label.setStyleSheet("color: #3498db; font-size: 16px; font-weight: bold;")
        close_btn = QPushButton("✕")
        close_btn.setFixedSize(30, 30)
        close_btn.setStyleSheet("""
            QPushButton {
                color: white; font-size: 18px; background-color: #e74c3c;
                border-radius: 15px; border: none;
            }
            QPushButton:hover { background-color: #c0392b; }
        """)
        close_btn.clicked.connect(self.close)
        title_row.addWidget(title_label)
        title_row.addStretch()
        title_row.addWidget(close_btn)
        frame_layout.addLayout(title_row)

        self.history_display = QTextEdit()
        self.history_display.setReadOnly(True)
        self.history_display.setStyleSheet("""
            QTextEdit {
                background-color: rgba(60, 60, 60, 200);
                color: #E0E0E0;
                border-radius: 8px;
                padding: 8px;
                font-size: 13px;
            }
        """)
        frame_layout.addWidget(self.history_display)

        input_layout = QHBoxLayout()
        self.question_input = QLineEdit()
        self.question_input.setPlaceholderText("输入您的问题...")
        self.question_input.setStyleSheet("""
            QLineEdit {
                background-color: #34495e;
                color: white;
                border-radius: 5px;
                padding: 8px;
                font-size: 13px;
            }
        """)
        self.question_input.setAttribute(Qt.WidgetAttribute.WA_InputMethodEnabled, True)  # 启用输入法
        self.send_btn = QPushButton("发送")
        self.send_btn.setFixedSize(60, 30)
        self.send_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db; color: white; border-radius: 5px;
            }
            QPushButton:hover { background-color: #2980b9; }
        """)
        self.send_btn.clicked.connect(self.on_send_clicked)
        input_layout.addWidget(self.question_input)
        input_layout.addWidget(self.send_btn)
        frame_layout.addLayout(input_layout)

        main_layout.addWidget(bg_frame)
        self.setLayout(main_layout)

        self.drag_position = None
        self.workers = []

    def extract_paragraphs(self):
        try:
            doc = fitz.open(self.pdf_path)
            full_text = ""
            for page in doc:
                full_text += page.get_text()
            doc.close()
            import re
            paras = re.split(r'[。\n]', full_text)
            paras = [p.strip() for p in paras if len(p.strip()) > 50]
            return paras
        except Exception as e:
            print(f"提取段落失败: {e}")
            return []

    def on_send_clicked(self):
        question = self.question_input.text().strip()
        if not question:
            return
        self.question_input.clear()
        self.history_display.append(f"<b style='color:#5dade2'>你:</b> {question}")
        self.send_btn.setEnabled(False)
        self.send_btn.setText("思考中...")
        self.worker = PdfChatWorker(self.pdf_path, question, self.paragraphs, self.bm25, parent=self)
        self.worker.finished.connect(self.on_answer_received)
        self.worker.error.connect(self.on_chat_error)
        self.worker.finished.connect(self.worker.deleteLater)
        self.worker.error.connect(self.worker.deleteLater)
        self.workers.append(self.worker)
        self.worker.start()

    def on_answer_received(self, answer):
        self.history_display.append(f"<b style='color:#f1c40f'>AI:</b> {answer}")
        self.send_btn.setEnabled(True)
        self.send_btn.setText("发送")

    def on_chat_error(self, error):
        self.history_display.append(f"<b style='color:#e74c3c'>错误:</b> {error}")
        self.send_btn.setEnabled(True)
        self.send_btn.setText("发送")

    def closeEvent(self, event):
        for worker in self.workers[:]:
            if worker.isRunning():
                try:
                    worker.finished.disconnect()
                except:
                    pass
                try:
                    worker.error.disconnect()
                except:
                    pass
                worker.quit()
                if not worker.wait(500):
                    worker.terminate()
                    worker.wait()
            worker.deleteLater()
        self.workers.clear()
        super().closeEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.drag_position = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event):
        if self.drag_position is not None:
            delta = event.globalPosition().toPoint() - self.drag_position
            self.move(self.pos() + delta)
            self.drag_position = event.globalPosition().toPoint()

    def mouseReleaseEvent(self, event):
        self.drag_position = None
