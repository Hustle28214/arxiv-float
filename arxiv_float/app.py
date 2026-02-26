# arxiv_float/app.py
import os
import sys
import threading
import time
from datetime import datetime

from PyQt6.QtWidgets import (QApplication, QWidget, QVBoxLayout, QLabel,
                             QScrollArea, QFrame, QHBoxLayout, QPushButton,
                             QMessageBox, QSystemTrayIcon, QMenu, QComboBox,
                             QDialog, QDialogButtonBox, QProgressDialog)
from PyQt6.QtCore import Qt, pyqtSignal, QSharedMemory, QMutex, QUrl
from PyQt6.QtGui import QFont, QCursor, QIcon, QAction, QPixmap, QPainter, QColor, QDesktopServices

import arxiv
from ollama import Client

# 绝对导入
from arxiv_float.utils.constants import *
from arxiv_float.utils.cache import CacheManager
from arxiv_float.utils.helpers import normalize_entry_id, open_url
from arxiv_float.ui.detail_window import DetailedSummaryWindow
from arxiv_float.ui.citation import CitationWindow
from arxiv_float.workers.citation import CitationWorker
from arxiv_float.ui.roadmap_global import RoadmapGlobalDialog
from arxiv_float.workers.roadmap_global import RoadmapGlobalWorker
from arxiv_float.ui.card import FloatingPaperCard

# Ollama 全局锁
ollama_lock = QMutex()


class ArxivFloatWindow(QWidget):
    add_signal = pyqtSignal(str, str, str, str, str, list)
    status_signal = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.cache_manager = CacheManager(CACHE_FILE, MAX_CACHE_SIZE)
        self.cache = self.cache_manager.cache
        self.last_cache_count = len(self.cache)
        self.detail_windows = []
        self.tray_icon = None
        self.current_period = "1年"
        self.init_ui()
        self.add_signal.connect(self.add_card)
        self.status_signal.connect(self.update_status)
        self.refresh_logic()
        self.create_tray_icon()

    def init_ui(self):
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setWindowTitle("Arxiv Float")

        screen = QApplication.primaryScreen().geometry()
        self.setGeometry(screen.width() - WINDOW_WIDTH - 20, 50, WINDOW_WIDTH, WINDOW_HEIGHT)

        self.main_layout = QVBoxLayout()
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # 导航栏
        self.navbar = QFrame()
        self.navbar.setStyleSheet("""
            QFrame {
                background-color: #2c3e50;
                border-top-left-radius: 15px;
                border-top-right-radius: 15px;
            }
        """)
        nav_layout = QHBoxLayout(self.navbar)

        self.title_label = QLabel("🤖 RobotRL 速递")
        self.title_label.setStyleSheet("color: white; font-weight: bold; font-size: 16px;")

        self.refresh_btn = QPushButton("🔄 刷新")
        self.refresh_btn.setFixedSize(80, 30)
        self.refresh_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.refresh_btn.setStyleSheet("""
            QPushButton {
                background-color: #3498db; color: white; border-radius: 5px; font-weight: bold;
            }
            QPushButton:hover { background-color: #2980b9; }
        """)
        self.refresh_btn.clicked.connect(self.refresh_logic)

        self.hot_btn = QPushButton("🔥 热门引用")
        self.hot_btn.setFixedSize(90, 30)
        self.hot_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.hot_btn.setStyleSheet("""
            QPushButton {
                background-color: #e67e22; color: white; border-radius: 5px; font-weight: bold;
            }
            QPushButton:hover { background-color: #d35400; }
        """)
        self.hot_btn.clicked.connect(self.show_citation_dialog)

        self.roadmap_global_btn = QPushButton("📈 全局路线图")
        self.roadmap_global_btn.setFixedSize(90, 30)
        self.roadmap_global_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.roadmap_global_btn.setStyleSheet("""
            QPushButton {
                background-color: #8e44ad; color: white; border-radius: 5px; font-weight: bold;
            }
            QPushButton:hover { background-color: #9b59b6; }
        """)
        self.roadmap_global_btn.clicked.connect(self.show_roadmap_global_dialog)

        self.close_btn = QPushButton("✕")
        self.close_btn.setFixedSize(30, 30)
        self.close_btn.setStyleSheet("color: white; font-size: 18px; background: transparent;")
        self.close_btn.clicked.connect(self.hide_to_tray)

        nav_layout.addWidget(self.title_label)
        nav_layout.addStretch()
        nav_layout.addWidget(self.roadmap_global_btn)
        nav_layout.addWidget(self.hot_btn)
        nav_layout.addWidget(self.refresh_btn)
        nav_layout.addWidget(self.close_btn)

        self.main_layout.addWidget(self.navbar)

        # 分类筛选行
        filter_layout = QHBoxLayout()
        filter_layout.setContentsMargins(15, 5, 15, 5)
        filter_label = QLabel("分类筛选:")
        filter_label.setStyleSheet("color: white; font-size: 12px;")
        self.category_combo = QComboBox()
        self.category_combo.addItem("全部")
        self.category_combo.setStyleSheet("""
            QComboBox {
                background-color: #34495e;
                color: white;
                border-radius: 5px;
                padding: 5px;
            }
            QComboBox::drop-down { border: none; }
            QComboBox::down-arrow { image: none; }
            QComboBox QAbstractItemView {
                background-color: #2c3e50;
                color: white;
                selection-background-color: #3498db;
                selection-color: white;
                outline: none;
            }
            QComboBox QAbstractItemView::item {
                min-height: 25px;
                padding: 4px;
            }
            QComboBox QAbstractItemView::item:hover {
                background-color: #3d566e;
            }
        """)
        self.category_combo.currentTextChanged.connect(self.filter_cards)
        filter_layout.addWidget(filter_label)
        filter_layout.addWidget(self.category_combo)
        filter_layout.addStretch()
        self.main_layout.addLayout(filter_layout)

        # 滚动区
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")
        self.scroll.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.content_widget = QWidget()
        self.content_widget.setStyleSheet("background: transparent;")
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.content_layout.setContentsMargins(15, 10, 15, 10)
        self.scroll.setWidget(self.content_widget)

        self.main_layout.addWidget(self.scroll)
        self.setLayout(self.main_layout)

    def create_tray_icon(self):
        icon = QIcon.fromTheme("applications-science")
        if icon.isNull():
            pixmap = QPixmap(64, 64)
            pixmap.fill(QColor(52, 152, 219))
            painter = QPainter(pixmap)
            painter.setPen(QColor(255, 255, 255))
            painter.setFont(QFont("Arial", 20))
            painter.drawText(pixmap.rect(), Qt.AlignmentFlag.AlignCenter, "ArX")
            painter.end()
            icon = QIcon(pixmap)

        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(icon)
        self.tray_icon.setToolTip("Arxiv Float")

        tray_menu = QMenu()
        show_action = QAction("显示窗口", self)
        show_action.triggered.connect(self.show_window)
        quit_action = QAction("退出", self)
        quit_action.triggered.connect(self.quit_app)

        tray_menu.addAction(show_action)
        tray_menu.addSeparator()
        tray_menu.addAction(quit_action)

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self.on_tray_activated)
        self.tray_icon.show()

    def on_tray_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.show_window()

    def show_window(self):
        self.show()
        self.raise_()
        self.activateWindow()

    def hide_to_tray(self):
        self.hide()
        self.tray_icon.showMessage(
            "Arxiv Float",
            "程序已最小化到系统托盘，双击图标可恢复。",
            QSystemTrayIcon.MessageIcon.Information,
            2000
        )

    def quit_app(self):
        self.tray_icon.hide()
        QApplication.quit()

    def closeEvent(self, event):
        event.ignore()
        self.hide_to_tray()

    def update_status(self, text):
        self.title_label.setText(text)

    def add_card(self, title, url, original_summary, ai_summary, entry_id, categories):
        card = FloatingPaperCard(title, url, original_summary, ai_summary)
        card.entry_id = entry_id
        card.set_categories(categories)
        card.show_detail_signal.connect(self.show_detail_window)
        self.content_layout.insertWidget(0, card)
        self.update_category_list()

    def show_detail_window(self, title, url, original_summary, ai_summary):
        if self.detail_windows:
            QMessageBox.information(self, "提示", "请先关闭当前打开的论文详情窗口，再打开新的。")
            return
        entry_id = normalize_entry_id(url)
        cached_data = self.cache_manager.get(entry_id) or {}
        cached_explanations = cached_data.get('full_explanations')
        cached_related = cached_data.get('related_papers')
        # 需要导入 detail_window，已在顶部导入
        detail_win = DetailedSummaryWindow(
            title, url, original_summary, ai_summary,
            cached_explanations=cached_explanations,
            cached_related=cached_related,
            cache_manager=self.cache_manager,
            parent=self
        )
        cursor_pos = QCursor.pos()
        detail_win.move(cursor_pos.x() + 20, cursor_pos.y() + 20)
        detail_win.show()
        self.detail_windows.append(detail_win)
        detail_win.destroyed.connect(
            lambda obj: self.detail_windows.remove(detail_win) if detail_win in self.detail_windows else None
        )

    def update_category_list(self):
        categories_set = set()
        for i in range(self.content_layout.count()):
            card = self.content_layout.itemAt(i).widget()
            if card and hasattr(card, 'categories'):
                categories_set.update(card.categories)
        current = self.category_combo.currentText()
        self.category_combo.clear()
        self.category_combo.addItem("全部")
        if categories_set:
            self.category_combo.addItems(sorted(categories_set))
        index = self.category_combo.findText(current)
        if index >= 0:
            self.category_combo.setCurrentIndex(index)

    def filter_cards(self, category):
        for i in range(self.content_layout.count()):
            card = self.content_layout.itemAt(i).widget()
            if card and hasattr(card, 'categories'):
                if category == "全部" or category in card.categories:
                    card.show()
                else:
                    card.hide()

    def refresh_logic(self):
        for i in reversed(range(self.content_layout.count())):
            widget = self.content_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)
        self.last_cache_count = len(self.cache_manager.cache)
        self.status_signal.emit(f"⚡ 正在同步... (缓存 {self.last_cache_count} 条)")
        threading.Thread(target=self.fetch_data, daemon=True).start()

    def fetch_data(self):
        try:
            # 检查 Ollama 服务
            import requests
            r = requests.get(f"{OLLAMA_HOST}/api/tags", timeout=2)
            if r.status_code != 200:
                raise Exception("服务返回错误")
        except Exception:
            self.status_signal.emit("❌ Ollama 未运行，请手动启动：ollama serve")
            return

        try:
            client = Client(host=OLLAMA_HOST)
            search = arxiv.Search(
                query=f"cat:{CATEGORY}",
                max_results=30,
                sort_by=arxiv.SortCriterion.SubmittedDate
            )

            new_entries = 0
            for r in arxiv.Client().results(search):
                entry_id = r.entry_id
                norm_id = normalize_entry_id(entry_id)
                title = r.title
                original_summary = r.summary

                cached = self.cache_manager.get(norm_id)

                if cached:
                    ai_summary = cached['summary']
                    categories = cached.get('categories', [])
                    if 'original_summary' not in cached:
                        self.cache_manager.update(norm_id, original_summary=original_summary)
                        new_entries += 1
                    print(f"命中缓存: {title[:30]}...")
                else:
                    print(f"未命中缓存，正在生成 AI 摘要: {title[:30]}...")
                    try:
                        ollama_lock.lock()
                        resp = client.chat(model=MODEL_NAME, messages=[
                            {'role': 'user', 'content': f"你是一个机器人专家。请用中文简述该论文创新点(80字以内):\n标题:{r.title}\n内容:{r.summary}"}
                        ])
                        ai_summary = resp['message']['content']

                        categories_prompt = f"""请根据以下论文标题和摘要，判断它最相关的技术领域，从下面列表中选择最合适的3-5个标签，用英文逗号分隔返回。只返回标签，不要任何其他文字或解释。

标签列表：{', '.join(CATEGORY_TAGS)}

标题：{r.title}
摘要：{r.summary}"""
                        cat_resp = client.chat(model=MODEL_NAME, messages=[{'role': 'user', 'content': categories_prompt}])
                        categories_text = cat_resp['message']['content']
                        raw_cats = [cat.strip() for cat in categories_text.split(',') if cat.strip()]
                        categories = []
                        seen = set()
                        for cat in raw_cats:
                            if cat in CATEGORY_TAGS and cat not in seen:
                                categories.append(cat)
                                seen.add(cat)
                        if not categories:
                            categories = ["Other"]
                    except Exception as e:
                        ai_summary = "AI 服务未启动或摘要失败"
                        categories = ["Other"]
                    finally:
                        ollama_lock.unlock()

                    self.cache_manager.update(
                        norm_id,
                        title=title,
                        summary=ai_summary,
                        original_summary=original_summary,
                        categories=categories,
                        full_explanations=None,
                        related_papers=None
                    )
                    new_entries += 1

                self.add_signal.emit(title, entry_id, original_summary, ai_summary, norm_id, categories)

            if new_entries > 0:
                self.cache_manager._save()

            added = len(self.cache_manager.cache) - self.last_cache_count
            cache_info = f"缓存 {len(self.cache_manager.cache)} 条"
            if added > 0:
                cache_info += f"，新增 {added} 条"
            self.status_signal.emit(f"✅ 更新于 {datetime.now().strftime('%H:%M')} ({cache_info})")
        except Exception as e:
            print(f"抓取数据异常: {e}")
            self.status_signal.emit(f"❌ 抓取失败 ({len(self.cache_manager.cache)} 条缓存)")

    def show_citation_dialog(self):
        dialog = QDialog(self)
        dialog.setWindowTitle("选择时间段")
        dialog.setFixedSize(300, 150)
        layout = QVBoxLayout(dialog)

        label = QLabel("请选择要查询的时间范围：")
        layout.addWidget(label)

        combo = QComboBox()
        combo.addItems(["3年", "2年", "1年", "6个月", "3个月"])
        layout.addWidget(combo)

        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(dialog.accept)
        button_box.rejected.connect(dialog.reject)
        layout.addWidget(button_box)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.current_period = combo.currentText()
            self.fetch_citations(self.current_period)

    def fetch_citations(self, period):
        self.progress = QProgressDialog("正在获取热门引用数据...", "取消", 0, 100, self)
        self.progress.setWindowModality(Qt.WindowModality.WindowModal)
        self.progress.show()

        self.citation_worker = CitationWorker(period, parent=self)
        self.citation_worker.progress.connect(self.update_citation_progress)
        self.citation_worker.finished.connect(self.show_citation_results)
        self.citation_worker.error.connect(self.show_citation_error)
        self.citation_worker.start()

    def update_citation_progress(self, value, total):
        self.progress.setMaximum(total)
        self.progress.setValue(value)

    def show_citation_results(self, papers):
        self.progress.close()
        if not papers:
            QMessageBox.information(self, "提示", "未找到符合条件的论文。")
            return
        self.citation_win = CitationWindow(papers, self.current_period)
        cursor_pos = QCursor.pos()
        self.citation_win.move(cursor_pos.x() + 20, cursor_pos.y() + 20)
        self.citation_win.show()

    def show_citation_error(self, error):
        self.progress.close()
        QMessageBox.critical(self, "错误", f"获取热门引用失败：{error}")

    def show_roadmap_global_dialog(self):
        dlg = RoadmapGlobalDialog(self.cache_manager, self)
        if dlg.exec() == QDialog.DialogCode.Accepted:
            category = dlg.category_combo.currentText()
            # 获取论文列表
            papers_info = []
            for entry_id, data in self.cache_manager.cache.items():
                if category == "全部" or category in data.get('categories', []):
                    # 尝试获取引言（如果有PDF则提取，否则用摘要）
                    intro = data.get('original_summary', '')
                    papers_info.append({
                        'title': data.get('title', ''),
                        'intro': intro,
                        'entry_id': entry_id
                    })
            if not papers_info:
                QMessageBox.information(self, "提示", "所选分类下没有论文。")
                return
            self.roadmap_worker = RoadmapGlobalWorker(papers_info, category, parent=self)
            self.roadmap_worker.finished.connect(self.show_roadmap_global_result)
            self.roadmap_worker.error.connect(self.show_roadmap_global_error)
            self.roadmap_worker.start()
            QMessageBox.information(self, "提示", f"正在生成 {category} 全局路线图，请稍候...")

    def show_roadmap_global_result(self, html):
        from arxiv_float.ui.roadmap_global import RoadmapGlobalWindow
        self.roadmap_win = RoadmapGlobalWindow(html)
        self.roadmap_win.show()

    def show_roadmap_global_error(self, error):
        QMessageBox.critical(self, "错误", f"生成路线图失败：{error}")

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.old_pos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event):
        if hasattr(self, 'old_pos'):
            delta = event.globalPosition().toPoint() - self.old_pos
            self.move(self.x() + delta.x(), self.y() + delta.y())
            self.old_pos = event.globalPosition().toPoint()


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("Arxiv Float")
    app.setQuitOnLastWindowClosed(False)

    # 单实例检查
    shared_memory = QSharedMemory("ArxivFloat_Instance_Key")
    if not shared_memory.create(1):
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Icon.Information)
        msg_box.setWindowTitle("Arxiv Float")
        msg_box.setText("程序已在运行中。")
        msg_box.setStandardButtons(QMessageBox.StandardButton.Ok)
        msg_box.exec()
        return 0

    font = QFont("PingFang SC", 10)
    app.setFont(font)
    window = ArxivFloatWindow()
    window.show()
    return app.exec()