import os
from pathlib import Path
import httpx
from ollama import Client

# --- 清除代理环境 (确保在任何可能使用代理的库导入前执行) ---
for key in ['http_proxy', 'https_proxy', 'all_proxy', 'HTTP_PROXY', 'HTTPS_PROXY', 'ALL_PROXY']:
    os.environ.pop(key, None)
os.environ['NO_PROXY'] = '127.0.0.1,localhost'

# --- 配置常量 ---
HOME = str(Path.home())

MODEL_NAME = "llama3.2"
CATEGORY = "cs.RO"
WINDOW_WIDTH = 700
WINDOW_HEIGHT = 900

# 缓存目录 ~/.cache/arxiv-float/
CACHE_DIR = os.path.join(HOME, ".cache", "arxiv-float")
os.makedirs(CACHE_DIR, exist_ok=True)
CACHE_FILE = os.path.join(CACHE_DIR, "arxiv_float_cache.json")
MAX_CACHE_SIZE = 50

# PDF 保存目录 ~/Documents/arxiv-float-papers/
PDF_SAVE_DIR = os.path.join(HOME, "Documents", "arxiv-float-papers")
os.makedirs(PDF_SAVE_DIR, exist_ok=True)

# 克隆项目目录 ~/arxiv-float-clones/
CLONE_BASE_DIR = os.path.join(HOME, "arxiv-float-clones")
os.makedirs(CLONE_BASE_DIR, exist_ok=True)

# Ollama 服务地址
OLLAMA_HOST = "http://127.0.0.1:11434"

# 扩展的分类标签
CATEGORY_TAGS = [
    "RL", "VLA", "AMP", "IL", "BC", "MPC", "LfD", "RLHF", "Offline RL", "IRL",
    "Imitation Learning", "Reinforcement Learning", "Inverse RL",
    "World Models", "Transformers", "Diffusion Models", "Generative Models",
    "VLM", "Vision-Language Models", "Large Language Models", "Multimodal",
    "Foundation Models", "Embodied AI", "Graph Neural Networks", "Attention",
    "Memory", "Causal Reasoning", "Generative AI",
    "Manipulation", "Locomotion", "Navigation", "Grasping", "Motion Planning",
    "Trajectory Optimization", "Planning", "Control", "Optimal Control",
    "Dynamics", "Sim-to-Real", "Domain Adaptation",
    "Computer Vision", "SLAM", "NLP", "Multi-Agent", "HRI", "Safety",
    "Explainability", "Ethics",
    "Soft Robotics", "Swarm", "Medical Robotics", "Agricultural Robotics",
    "Autonomous Driving", "Drone", "Simulation", "Real-world", "Deployment",
    "Hardware",
    "Meta-Learning", "Few-Shot", "Multi-Task", "Self-Supervised Learning",
    "Supervised Learning", "Unsupervised Learning",
    "Brain-inspired Computing", "Neuromorphic Computing", "Mimic Learning", "Transfer Learning",
    "Other"
]

# 注意：目录已在上面各路径处创建，不再需要额外的 os.makedirs

def create_ollama_client():
    """创建 Ollama 客户端（禁用代理已在程序启动时处理）"""
    from ollama import Client
    return Client(host=OLLAMA_HOST)