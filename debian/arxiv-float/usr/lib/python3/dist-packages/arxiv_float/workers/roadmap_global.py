# arxiv_float/workers/roadmap_global.py
from PyQt6.QtCore import QThread, pyqtSignal
from ..utils.constants import create_ollama_client, MODEL_NAME

class RoadmapGlobalWorker(QThread):
    finished = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, papers_info, main_category, parent=None):
        """
        papers_info: list of dict, each with keys 'title' and 'intro'
        main_category: str, the technology category to analyze
        """
        super().__init__(parent)
        self.papers_info = papers_info
        self.main_category = main_category

    def markdown_to_html(self, text):
        """极简 Markdown 转 HTML"""
        lines = text.split('\n')
        html_lines = []
        in_list = False
        for line in lines:
            if line.startswith('# '):
                html_lines.append(f'<h1>{line[2:]}</h1>')
            elif line.startswith('## '):
                html_lines.append(f'<h2>{line[3:]}</h2>')
            elif line.startswith('### '):
                html_lines.append(f'<h3>{line[4:]}</h3>')
            elif line.startswith('- ') or line.startswith('* '):
                if not in_list:
                    html_lines.append('<ul>')
                    in_list = True
                html_lines.append(f'<li>{line[2:]}</li>')
            else:
                if in_list:
                    html_lines.append('</ul>')
                    in_list = False
                html_lines.append(f'<p>{line}</p>')
        if in_list:
            html_lines.append('</ul>')
        return ''.join(html_lines)

    def run(self):
        try:
            context = "\n\n".join([
                f"标题：{p['title']}\n引言：{p['intro'][:1000]}" for p in self.papers_info
            ])
            prompt = f"""你是一位机器人领域的专家。请根据以下多篇论文的引言部分，分析“{self.main_category}”领域的发展脉络、关键技术和未来趋势。
要求生成包含时间线、主要分支和代表工作的路线图。使用 Markdown 格式。

论文信息：
{context}

请输出详细的路线图。"""
            client = create_ollama_client()
            resp = client.chat(model=MODEL_NAME, messages=[{'role': 'user', 'content': prompt}])
            roadmap = resp['message']['content']
            html = self.markdown_to_html(roadmap)
            self.finished.emit(html)
        except Exception as e:
            self.error.emit(str(e))
