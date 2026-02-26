from setuptools import setup, find_packages

setup(
    name='arxiv-float',
    version='1.0.0',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'PyQt6',
        'arxiv',
        'ollama',
        'PyMuPDF',
        'requests',
        'rank_bm25',
    ],
    entry_points={
        'console_scripts': [
            'arxiv-float = run:main',
        ],
    },
)
