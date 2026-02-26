# arxiv_float/ui/detail_window.py
import os
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QFrame, QScrollArea, QMessageBox,
                             QTextEdit)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QCursor

from .full_explanation import FullExplanationWindow
from .related_papers import RelatedPapersWindow
from .pdf_chat import PdfChatWindow
from ..workers.download import PdfDownloadWorker
from ..workers.explanation import ExplanationWorker
from ..workers.related import RelatedPapersWorker
from ..workers.code_search import CodeSearchWorker
from ..workers.git_clone import GitCloneWorker
from ..utils.constants import PDF_SAVE_DIR, CLONE_BASE_DIR
from ..utils.helpers import sanitize_filename, normalize_entry_id, open_url, extract_arxiv_id_from_url


class DetailedSummaryWindow(QWidget):
    cache_update_signal = pyqtSignal(str, str, object)

    def __init__(self, title, arxiv_url, original_summary, ai_summary,
                 cached_explanations=None, cached_related=None,
                 cache_manager=None, parent=None):
        super().__init__(parent)
        self.title = title
        self.url = arxiv_url
        self.original_summary = original_summary
        self.ai_summary = ai_summary
        self.arxiv_id = extract_arxiv_id_from_url(arxiv_url)
        self.entry_id = normalize_entry_id(arxiv_url)
        self.pdf_path = None
        self.workers = []
        self.cached_explanations = cached_explanations
        self.cached_related = cached_related
        self.cache_manager = cache_manager
        self.busy = False

        # 自动检测本地是否已有 PDF
        if self.arxiv_id:
            expected_filename = sanitize_filename(self.title) + ".pdf"
            expected_path = os.path.join(PDF_SAVE_DIR, expected_filename)
            if os.path.exists(expected_path):
                self.pdf_path = expected_path

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        self.setFixedSize(480, 720)

        # UI 构建
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(0)

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
        frame_layout.setSpacing(10)

        # 标题行
        title_row = QHBoxLayout()
        title_label = QLabel(title)
        title_label.setWordWrap(True)
        title_label.setStyleSheet("color: #3498db; font-size: 18px; font-weight: bold;")
        title_label.setCursor(Qt.CursorShape.PointingHandCursor)
        title_label.mousePressEvent = lambda e: open_url(arxiv_url)
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

        # 第一行按钮
        button_row1 = QHBoxLayout()
        self.download_btn = QPushButton("📥 PDF下载")
        self.explain_btn = QPushButton("📖 全文解释")
        self.related_btn = QPushButton("🔗 相关论文")
        for btn in (self.download_btn, self.explain_btn, self.related_btn):
            btn.setFixedHeight(30)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #2c3e50; color: white; border-radius: 5px;
                    font-size: 12px; padding: 5px;
                }
                QPushButton:hover { background-color: #34495e; }
            """)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
        button_row1.addWidget(self.download_btn)
        button_row1.addWidget(self.explain_btn)
        button_row1.addWidget(self.related_btn)
        frame_layout.addLayout(button_row1)

        # 第二行按钮
        button_row2 = QHBoxLayout()
        self.chat_btn = QPushButton("💬 Chat with PDF")
        self.code_btn = QPushButton("🔗 查看代码")
        self.chat_btn.setEnabled(self.pdf_path is not None)  # 如果已有 PDF 则启用
        self.code_btn.setEnabled(True)
        for btn in (self.chat_btn, self.code_btn):
            btn.setFixedHeight(30)
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #27ae60; color: white; border-radius: 5px;
                    font-size: 12px; padding: 5px;
                }
                QPushButton:hover { background-color: #2ecc71; }
                QPushButton:disabled { background-color: #7f8c8d; }
            """)
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
        button_row2.addWidget(self.chat_btn)
        button_row2.addWidget(self.code_btn)
        frame_layout.addLayout(button_row2)

        if self.cached_explanations:
            self.explain_btn.setText("📖 查看缓存解释")
        if self.cached_related:
            self.related_btn.setText("🔗 查看缓存相关论文")

        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet("color: #555;")
        frame_layout.addWidget(line)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        scroll_content = QWidget()
        scroll_content.setStyleSheet("background: transparent;")
        scroll_layout = QVBoxLayout(scroll_content)
        scroll_layout.setContentsMargins(0, 0, 5, 0)
        scroll_layout.setSpacing(10)

        ai_label = QLabel("🤖 AI 解读")
        ai_label.setStyleSheet("color: #aaa; font-size: 14px; font-weight: bold;")
        scroll_layout.addWidget(ai_label)

        ai_content = QLabel(ai_summary)
        ai_content.setWordWrap(True)
        ai_content.setStyleSheet("color: #E0E0E0; font-size: 14px; line-height: 150%;")
        scroll_layout.addWidget(ai_content)

        sep_line = QFrame()
        sep_line.setFrameShape(QFrame.Shape.HLine)
        sep_line.setStyleSheet("color: #444;")
        scroll_layout.addWidget(sep_line)

        orig_label = QLabel("📄 原始摘要")
        orig_label.setStyleSheet("color: #aaa; font-size: 14px; font-weight: bold;")
        scroll_layout.addWidget(orig_label)

        orig_content = QLabel(original_summary)
        orig_content.setWordWrap(True)
        orig_content.setStyleSheet("color: #ccc; font-size: 13px; line-height: 150%;")
        scroll_layout.addWidget(orig_content)

        scroll_layout.addStretch()
        scroll.setWidget(scroll_content)
        frame_layout.addWidget(scroll)

        main_layout.addWidget(bg_frame)
        self.setLayout(main_layout)

        # 连接信号
        self.download_btn.clicked.connect(self.download_pdf)
        self.explain_btn.clicked.connect(self.explain_full_text)
        self.related_btn.clicked.connect(self.find_related_papers)
        self.chat_btn.clicked.connect(self.open_chat_window)
        self.code_btn.clicked.connect(self.search_code)

        self.drag_position = None

    # ---------- 忙碌管理 ----------
    def set_busy(self, busy):
        self.busy = busy
        self.download_btn.setEnabled(not busy)
        self.explain_btn.setEnabled(not busy)
        self.related_btn.setEnabled(not busy)
        self.chat_btn.setEnabled(not busy and self.pdf_path is not None)
        self.code_btn.setEnabled(not busy)

    def check_busy(self):
        if self.busy:
            QMessageBox.information(self, "提示", "正在处理中，请稍候...")
            return True
        return False

    # ---------- PDF下载 ----------
    def download_pdf(self):
        if self.check_busy():
            return
        if not self.arxiv_id:
            QMessageBox.warning(self, "错误", "无法提取arXiv ID")
            return
        self.set_busy(True)
        self.download_btn.setText("下载中...")
        self.download_worker = PdfDownloadWorker(self.arxiv_id, self.title, parent=self)
        self.download_worker.finished.connect(self.on_download_finished)
        self.download_worker.finished.connect(self.download_worker.deleteLater)
        self.workers.append(self.download_worker)
        self.download_worker.start()

    def on_download_finished(self, success, path, error, already_exists):
        self.download_btn.setText("📥 PDF下载")
        if success:
            self.pdf_path = path
            self.chat_btn.setEnabled(True)
            if already_exists:
                QMessageBox.information(self, "提示", f"PDF已存在：{path}")
            else:
                QMessageBox.information(self, "下载成功", f"PDF已保存至：{path}")
        else:
            QMessageBox.critical(self, "下载失败", error)
        self.set_busy(False)

    # ---------- 全文解释 ----------
    def explain_full_text(self):
        if self.check_busy():
            return
        if self.cached_explanations:
            self.show_explanation(self.cached_explanations)
            return
        if not self.pdf_path or not os.path.exists(self.pdf_path):
            QMessageBox.information(self, "提示", "请先下载PDF，然后再次点击“全文解释”。")
            return
        self.set_busy(True)
        self.explain_btn.setText("解析中...")
        self.worker = ExplanationWorker(self.pdf_path, self.title, self.url, parent=self)
        self.worker.finished.connect(self.show_explanation)
        self.worker.error.connect(self.on_explain_error)
        self.worker.finished.connect(self.worker.deleteLater)
        self.worker.error.connect(self.worker.deleteLater)
        self.workers.append(self.worker)
        self.worker.start()
        QMessageBox.information(self, "提示", "正在解析全文，请稍候...")

    def on_explain_error(self, error):
        self.explain_btn.setText("📖 全文解释")
        QMessageBox.critical(self, "解释失败", error)
        self.set_busy(False)

    def show_explanation(self, explanations):
        self.explain_btn.setText("📖 全文解释")
        if self.cache_manager:
            self.cache_manager.update(self.entry_id, full_explanations=explanations)
        self.exp_win = FullExplanationWindow(explanations)
        cursor_pos = QCursor.pos()
        self.exp_win.move(cursor_pos.x() + 20, cursor_pos.y() + 20)
        self.exp_win.show()
        self.set_busy(False)

    # ---------- 相关论文 ----------
    def find_related_papers(self):
        if self.check_busy():
            return
        if self.cached_related:
            self.show_related_papers(self.cached_related)
            return
        if not self.pdf_path or not os.path.exists(self.pdf_path):
            QMessageBox.information(self, "提示", "请先下载PDF，然后再次点击“相关论文”。")
            return
        self.set_busy(True)
        self.related_btn.setText("分析中...")
        self.worker2 = RelatedPapersWorker(self.pdf_path, self.title, parent=self)
        self.worker2.finished.connect(self.show_related_papers)
        self.worker2.error.connect(self.on_related_error)
        self.worker2.finished.connect(self.worker2.deleteLater)
        self.worker2.error.connect(self.worker2.deleteLater)
        self.workers.append(self.worker2)
        self.worker2.start()
        QMessageBox.information(self, "提示", "正在分析引文，请稍候...")

    def on_related_error(self, error):
        self.related_btn.setText("🔗 相关论文")
        QMessageBox.critical(self, "分析失败", error)
        self.set_busy(False)

    def show_related_papers(self, papers):
        self.related_btn.setText("🔗 相关论文")
        if not papers:
            QMessageBox.information(self, "提示", "未找到相关论文或提取失败。")
            self.set_busy(False)
            return
        if self.cache_manager:
            self.cache_manager.update(self.entry_id, related_papers=papers)
        self.rel_win = RelatedPapersWindow(papers)
        cursor_pos = QCursor.pos()
        self.rel_win.move(cursor_pos.x() + 20, cursor_pos.y() + 20)
        self.rel_win.show()
        self.set_busy(False)

    # ---------- 聊天 ----------
    def open_chat_window(self):
        if self.check_busy():
            return
        if not self.pdf_path or not os.path.exists(self.pdf_path):
            QMessageBox.information(self, "提示", "请先下载PDF。")
            return
        self.chat_win = PdfChatWindow(self.pdf_path, self.title, parent=self)
        cursor_pos = QCursor.pos()
        self.chat_win.move(cursor_pos.x() + 20, cursor_pos.y() + 20)
        self.chat_win.show()

    # ---------- 代码查询 ----------
    def search_code(self):
        if self.check_busy():
            return
        if not self.arxiv_id:
            QMessageBox.warning(self, "错误", "无法提取arXiv ID")
            return
        self.set_busy(True)
        self.code_btn.setText("查询中...")
        self.code_worker = CodeSearchWorker(self.arxiv_id, parent=self)
        self.code_worker.finished.connect(self.on_code_found)
        self.code_worker.error.connect(self.on_code_error)
        self.code_worker.finished.connect(self.code_worker.deleteLater)
        self.code_worker.error.connect(self.code_worker.deleteLater)
        self.workers.append(self.code_worker)
        self.code_worker.start()

    def on_code_found(self, data):
        self.code_btn.setText("🔗 查看代码")
        repo_url = data['repository_url']
        msg = QMessageBox(self)
        msg.setWindowTitle("找到代码仓库")
        msg.setText(f"仓库地址：{repo_url}\n\n请选择操作：")
        msg.setIcon(QMessageBox.Icon.Question)
        open_btn = msg.addButton("打开网页", QMessageBox.ButtonRole.AcceptRole)
        clone_btn = msg.addButton("Git Clone", QMessageBox.ButtonRole.ActionRole)
        cancel_btn = msg.addButton("取消", QMessageBox.ButtonRole.RejectRole)
        msg.exec()
        if msg.clickedButton() == open_btn:
            open_url(repo_url)
        elif msg.clickedButton() == clone_btn:
            safe_title = sanitize_filename(self.title)
            target_dir = os.path.join(CLONE_BASE_DIR, safe_title)
            reply = QMessageBox.question(self, "确认克隆", f"将克隆到：{target_dir}\n继续吗？",
                                         QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.Yes:
                self.start_clone(repo_url, target_dir)
        self.set_busy(False)

    def on_code_error(self, error):
        self.code_btn.setText("🔗 查看代码")
        QMessageBox.information(self, "代码查询", f"未找到代码仓库：{error}")
        self.set_busy(False)

    def start_clone(self, repo_url, target_dir):
        self.set_busy(True)
        self.clone_worker = GitCloneWorker(repo_url, target_dir, parent=self)
        self.clone_worker.finished.connect(self.on_clone_finished)
        self.clone_worker.error.connect(self.on_clone_error)
        self.clone_worker.finished.connect(self.clone_worker.deleteLater)
        self.clone_worker.error.connect(self.clone_worker.deleteLater)
        self.workers.append(self.clone_worker)
        self.clone_worker.start()
        QMessageBox.information(self, "克隆中", f"正在克隆到 {target_dir}，请稍候...")

    def on_clone_finished(self, target_dir):
        QMessageBox.information(self, "克隆完成", f"代码已克隆到：{target_dir}")
        self.set_busy(False)

    def on_clone_error(self, error):
        QMessageBox.critical(self, "克隆失败", error)
        self.set_busy(False)

    def closeEvent(self, event):
        """安全关闭窗口，停止所有工作线程"""
        # 复制列表以避免迭代时修改
        workers_to_stop = self.workers[:]
        for worker in workers_to_stop:
            try:
                if worker is not None:
                    if worker.isRunning():
                        worker.requestInterruption()
                        try:
                            worker.finished.disconnect()
                        except:
                            pass
                        try:
                            worker.error.disconnect()
                        except:
                            pass
                        if not worker.wait(2000):
                            worker.terminate()
                            worker.wait()
                    worker.deleteLater()
            except RuntimeError as e:
                # 对象可能已被删除，忽略
                print(f"关闭时忽略已删除对象: {e}")
            except Exception as e:
                print(f"关闭工作线程时出错: {e}")
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