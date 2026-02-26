# Arxiv Float: AI 驱动的 arXiv 论文阅读助手

[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)

Arxiv Float 是一款面向机器人/人工智能领域研究者的桌面应用，能够实时获取 arXiv 最新论文，利用大语言模型生成中文摘要，并提供 PDF 聊天、代码仓库查询、全局技术路线图等深度功能，帮助您快速把握领域动态。

## ✨ 功能特性

- 📥 **实时论文流** – 自动抓取 `cs.RO` 分类最新论文，支持分类标签筛选。（您可以在源代码修改需要的分类，默认支持Robotics。）
- 🤖 **AI 摘要** – 调用本地 Ollama 服务（默认模型为 `llama3.2`）生成中文创新点简述。
- 🏷️ **智能分类** – 自动为论文打上技术领域标签（RL、VLA、世界模型等）。
- 📄 **PDF 深度交互**  
  - 下载论文 PDF  
  - 全文章节解释（引言、方法、实验等）  
  - 基于检索的 PDF 聊天（支持 BM25 检索）  
  - 分析参考文献，推荐相关论文
- 🔗 **代码仓库集成**  
  - 通过 Papers with Code API 查找代码仓库  
  - 一键打开仓库网页或 Git Clone 到本地
- 📈 **全局技术路线图** – 基于缓存论文生成指定技术领域的发展脉络
- 🔥 **热门引用排行** – 按时间段筛选高引用论文
- 🖥️ **支持后台运行** – 可隐藏至托盘，后台运行

## 🛠️ 安装与运行

### 前置要求

- **Python 3.10+**
- **[Ollama](https://ollama.com/)** – 本地运行大语言模型，并下载`llama3.2`：
```bash
ollama serve
ollama run llama3.2
```
### 自定义

你可以通过修改`constant.py`来自定义所使用的模型和文章类别：

```python
MODEL_NAME = "llama3.2"
CATEGORY = "cs.RO"
```

你可以修改ollama运行端口来防止冲突：
```python
OLLAMA_HOST = "http://127.0.0.1:11434"
```

分类标签提供了众多预选，您也可以进一步自定义：
```python
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
```

同样地，您可以将缓存目录与下载目录改到您希望的：

```python
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

```