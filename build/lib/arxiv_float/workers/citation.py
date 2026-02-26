import time
import requests
import arxiv
from datetime import datetime
from PyQt6.QtCore import QThread, pyqtSignal
from ..utils.constants import CATEGORY
from ..utils.helpers import extract_arxiv_id_from_url, get_date_range

class CitationWorker(QThread):
    progress = pyqtSignal(int, int)
    finished = pyqtSignal(list)
    error = pyqtSignal(str)

    def __init__(self, period, parent=None):
        super().__init__(parent)
        self.period = period

    def run(self):
        try:
            start_date = get_date_range(self.period)
            end_date = datetime.now().strftime("%Y%m%d") + "235959"
            query = f"cat:{CATEGORY} AND submittedDate:[{start_date} TO {end_date}]"
            search = arxiv.Search(
                query=query,
                max_results=200,
                sort_by=arxiv.SortCriterion.SubmittedDate,
                sort_order=arxiv.SortOrder.Descending
            )

            papers = []
            client = arxiv.Client()
            for i, result in enumerate(client.results(search)):
                if i >= 200:
                    break
                papers.append({
                    'entry_id': result.entry_id,
                    'title': result.title,
                    'authors': ', '.join(a.name for a in result.authors),
                    'year': result.published.year,
                    'url': result.entry_id,
                    'summary': result.summary,
                    'citationCount': 0
                })
                self.progress.emit(i+1, 200)

            total = len(papers)
            for idx, paper in enumerate(papers):
                arxiv_id = extract_arxiv_id_from_url(paper['entry_id'])
                if arxiv_id:
                    url = f"https://api.semanticscholar.org/graph/v1/paper/arXiv:{arxiv_id}?fields=citationCount"
                    try:
                        resp = requests.get(url, timeout=5)
                        if resp.status_code == 200:
                            data = resp.json()
                            paper['citationCount'] = data.get('citationCount', 0)
                    except Exception:
                        paper['citationCount'] = 0
                time.sleep(0.1)
                self.progress.emit(total + idx + 1, total * 2)

            sorted_papers = sorted(papers, key=lambda x: x['citationCount'], reverse=True)[:50]
            self.finished.emit(sorted_papers)
        except Exception as e:
            self.error.emit(str(e))
