# arxiv_float/ui/card.py
from PyQt6.QtWidgets import (QFrame, QVBoxLayout, QHBoxLayout, QLabel,
                             QPushButton, QWidget)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QCursor
from ..utils.helpers import open_url

class FloatingPaperCard(QFrame):
    show_detail_signal = pyqtSignal(str, str, str, str)

    def __init__(self, title, url, original_summary, ai_summary):
        super().__init__()
        self.title = title
        self.url = url
        self.original_summary = original_summary
        self.ai_summary = ai_summary
        self.entry_id = None
        self.categories = []

        layout = QVBoxLayout()
        layout.setSpacing(8)

        # 标题行
        title_row = QHBoxLayout()
        t_label = QLabel(title)
        t_label.setWordWrap(True)
        t_label.setStyleSheet("color: #3498db; font-weight: bold; font-size: 18px; border: none;")
        t_label.setCursor(Qt.CursorShape.PointingHandCursor)
        t_label.mousePressEvent = lambda e: open_url(url)

        detail_btn = QPushButton("🔍")
        detail_btn.setFixedSize(30, 30)
        detail_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #3498db;
                font-size: 16px;
                border: none;
            }
            QPushButton:hover {
                color: #5dade2;
                background-color: rgba(255,255,255,0.1);
                border-radius: 15px;
            }
        """)
        detail_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        detail_btn.clicked.connect(self.emit_detail_signal)
        title_row.addWidget(t_label)
        title_row.addStretch()
        title_row.addWidget(detail_btn)

        # AI 摘要
        s_label = QLabel(ai_summary)
        s_label.setWordWrap(True)
        s_label.setStyleSheet("color: #E0E0E0; font-size: 15px; line-height: 150%; border: none; background: transparent;")

        # 分类标签行
        self.categories_widget = QWidget()
        self.categories_widget.setVisible(False)
        self.categories_layout_inner = QHBoxLayout(self.categories_widget)
        self.categories_layout_inner.setContentsMargins(0, 0, 0, 0)
        self.categories_layout_inner.setSpacing(5)

        layout.addLayout(title_row)
        layout.addWidget(s_label)
        layout.addWidget(self.categories_widget)
        self.setLayout(layout)

        self.setStyleSheet("""
            QFrame {
                background-color: rgba(45, 45, 45, 220);
                border-radius: 12px;
                padding: 15px;
                margin-bottom: 15px;
                border: 1px solid rgba(255, 255, 255, 0.1);
            }
            QFrame:hover {
                background-color: rgba(60, 60, 60, 240);
                border: 1px solid #3498db;
            }
        """)

    def set_categories(self, categories):
        self.categories = categories
        # 清除旧标签
        for i in reversed(range(self.categories_layout_inner.count())):
            widget = self.categories_layout_inner.itemAt(i).widget()
            if widget:
                widget.deleteLater()
        if categories:
            for cat in categories[:5]:  # 最多显示5个
                label = QLabel(cat)
                label.setStyleSheet("""
                    background-color: #3498db;
                    color: white;
                    border-radius: 10px;
                    padding: 3px 8px;
                    font-size: 11px;
                    font-weight: bold;
                """)
                self.categories_layout_inner.addWidget(label)
            self.categories_layout_inner.addStretch()
            self.categories_widget.setVisible(True)
        else:
            self.categories_widget.setVisible(False)

    def emit_detail_signal(self):
        self.show_detail_signal.emit(self.title, self.url, self.original_summary, self.ai_summary)
