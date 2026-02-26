from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QScrollArea, QFrame, QHBoxLayout, QPushButton
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QCursor
from ..utils.helpers import open_url  # 稍后我们会定义 open_url 函数

class RelatedPapersWindow(QWidget):
    def __init__(self, papers, parent=None):
        super().__init__(parent)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(500, 600)

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
        title_label = QLabel("🔗 最相关的10篇论文")
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

        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setStyleSheet("color: #555;")
        frame_layout.addWidget(line)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        content_widget = QWidget()
        content_widget.setStyleSheet("background: transparent;")
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(0, 0, 5, 0)
        content_layout.setSpacing(10)

        for paper in papers:
            card = QFrame()
            card.setStyleSheet("""
                QFrame {
                    background-color: rgba(60, 60, 60, 200);
                    border-radius: 10px;
                    padding: 10px;
                }
                QFrame:hover { background-color: rgba(80, 80, 80, 220); }
            """)
            card_layout = QVBoxLayout(card)

            title = QLabel(paper['title'])
            title.setWordWrap(True)
            title.setStyleSheet("color: #5dade2; font-size: 14px; font-weight: bold;")
            title.setCursor(Qt.CursorShape.PointingHandCursor)
            title.mousePressEvent = lambda e, url=paper['url']: open_url(url)
            card_layout.addWidget(title)

            reason = QLabel(paper['reason'])
            reason.setWordWrap(True)
            reason.setStyleSheet("color: #ccc; font-size: 12px;")
            card_layout.addWidget(reason)

            content_layout.addWidget(card)

        content_layout.addStretch()
        scroll.setWidget(content_widget)
        frame_layout.addWidget(scroll)

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
