# setup.py
from setuptools import setup, find_packages

setup(
    name="truth-talent",
    version="1.0.0",
    packages=find_packages(),
    install_requires=[
        "fastapi==0.104.1",
        "uvicorn[standard]==0.24.0", 
        "python-multipart==0.0.6",
        "pdfplumber==0.10.3",
        "python-docx==1.1.0",
        "supabase==2.3.1",
        "regex==2023.12.25",
    ],
    python_requires=">=3.8",
)