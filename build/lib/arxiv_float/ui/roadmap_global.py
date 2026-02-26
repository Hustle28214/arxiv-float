# arxiv_float/ui/roadmap_global.py
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                             QComboBox, QDialogButtonBox, QTextEdit,
                             QPushButton, QFrame, QWidget)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QCursor

from ..utils.constants import CATEGORY_TAGS


class RoadmapGlobalDialog(QDialog):
    """选择分类和时间范围的对话框"""
    def __init__(self, cache_manager, parent=None):
        super().__init__(parent)
        self.cache_manager = cache_manager
        self.setWindowTitle("生成全局技术路线图")
        self.setFixedSize(400, 200)

        layout = QVBoxLayout(self)

        # 分类选择
        label = QLabel("选择技术分类：")
        layout.addWidget(label)

        self.category_combo = QComboBox()
        self.category_combo.addItem("全部")  # 全部分类
        # 从缓存中提取所有存在的分类
        categories_set = set()
        for _, data in cache_manager.cache.items():
            cats = data.get('categories', [])
            categories_set.update(cats)
        # 添加存在的分类，并按字母排序
        for cat in sorted(categories_set):
            if cat and cat != "Other":
                self.category_combo.addItem(cat)
        # 最后添加 Other
        if "Other" in categories_set:
            self.category_combo.addItem("Other")
        layout.addWidget(self.category_combo)

        # 按钮
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok |
                                      QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)


class RoadmapGlobalWindow(QWidget):
    """显示全局路线图的窗口"""
    def __init__(self, html_content, parent=None):
        super().__init__(parent)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(600, 700)

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

        # 标题行
        title_row = QHBoxLayout()
        title_label = QLabel("📈 全局技术路线图")
        title_label.setStyleSheet("color: #3498db; font-size: 18px; font-weight: bold;")
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

        # 内容显示区
        self.text_display = QTextEdit()
        self.text_display.setReadOnly(True)
        self.text_display.setStyleSheet("""
            QTextEdit {
                background-color: rgba(60, 60, 60, 200);
                color: #E0E0E0;
                border-radius: 8px;
                padding: 8px;
                font-size: 13px;
            }
        """)
        self.text_display.setHtml(html_content)
        frame_layout.addWidget(self.text_display)

        main_layout.addWidget(bg_frame)
        self.setLayout(main_layout)

        self.drag_position = None

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
