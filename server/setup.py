from setuptools import setup, find_packages

setup(
    name="arxival",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        "arxiv",
        "aiohttp",
        "beautifulsoup4",
        "PyPDF2",
        "pytest",
        "pytest-asyncio",
    ],
)
