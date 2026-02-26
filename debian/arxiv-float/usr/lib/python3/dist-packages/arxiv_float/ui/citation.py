from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QScrollArea, QFrame, QHBoxLayout, QPushButton
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QCursor
from ..utils.helpers import open_url

class CitationWindow(QWidget):
    def __init__(self, papers, period, parent=None):
        super().__init__(parent)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setFixedSize(550, 650)

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
        title_label = QLabel(f"🔥 近{period}引用量Top 50")
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

        for i, paper in enumerate(papers, 1):
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

            title_line = QHBoxLayout()
            rank_label = QLabel(f"#{i}")
            rank_label.setStyleSheet("color: #e67e22; font-size: 14px; font-weight: bold;")
            title_line.addWidget(rank_label)

            title = QLabel(paper['title'])
            title.setWordWrap(True)
            title.setStyleSheet("color: #5dade2; font-size: 14px; font-weight: bold;")
            title.setCursor(Qt.CursorShape.PointingHandCursor)
            title.mousePressEvent = lambda e, url=paper['url']: open_url(url)
            title_line.addWidget(title, 1)

            citations = QLabel(f"📊 {paper['citationCount']}")
            citations.setStyleSheet("color: #f1c40f; font-size: 13px;")
            title_line.addWidget(citations)

            card_layout.addLayout(title_line)

            info = QLabel(f"{paper.get('authors', '')} | {paper.get('year', '')}")
            info.setWordWrap(True)
            info.setStyleSheet("color: #aaa; font-size: 11px;")
            card_layout.addWidget(info)

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
