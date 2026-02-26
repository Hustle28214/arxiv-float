import json
import threading
import time
from .helpers import normalize_entry_id

class CacheManager:
    """线程安全的缓存管理器"""
    def __init__(self, cache_file, max_size=50):
        self.cache_file = cache_file
        self.max_size = max_size
        self.lock = threading.Lock()
        self.cache = self._load()

    def _load(self):
        try:
            with open(self.cache_file, 'r', encoding='utf-8') as f:
                raw_cache = json.load(f)
            new_cache = {}
            for key, value in raw_cache.items():
                norm_key = normalize_entry_id(key)
                # 确保所有必要字段存在
                if 'original_summary' not in value:
                    value['original_summary'] = ''
                if 'categories' not in value:
                    value['categories'] = []
                if 'full_explanations' not in value:
                    value['full_explanations'] = None
                if 'related_papers' not in value:
                    value['related_papers'] = None
                new_cache[norm_key] = value
            print(f"缓存加载成功，共 {len(new_cache)} 条")
            return new_cache
        except FileNotFoundError:
            print("缓存文件不存在，将创建新缓存")
            return {}
        except json.JSONDecodeError as e:
            print(f"缓存文件损坏，将重置缓存: {e}")
            return {}
        except Exception as e:
            print(f"加载缓存时发生未知错误: {e}")
            return {}

    def _save(self):
        if len(self.cache) > self.max_size:
            sorted_items = sorted(self.cache.items(), key=lambda x: x[1].get('timestamp', 0))
            to_remove = sorted_items[:len(self.cache) - self.max_size]
            for entry_id, _ in to_remove:
                del self.cache[entry_id]
        try:
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.cache, f, ensure_ascii=False, indent=2)
            print("缓存已保存")
        except Exception as e:
            print(f"保存缓存失败: {e}")

    def get(self, entry_id):
        norm_id = normalize_entry_id(entry_id)
        with self.lock:
            return self.cache.get(norm_id)

    def update(self, entry_id, **kwargs):
        norm_id = normalize_entry_id(entry_id)
        with self.lock:
            if norm_id not in self.cache:
                self.cache[norm_id] = {}
            self.cache[norm_id].update(kwargs)
            self.cache[norm_id]['timestamp'] = time.time()
        self._save()

    def all_items(self):
        with self.lock:
            return list(self.cache.items())
