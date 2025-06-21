"""
Setup script for common package
"""
from setuptools import setup, find_packages

setup(
    name="common",
    version="0.1.0",
    description="Common utilities for AI Voice Agent services",
    author="AI Voice Agent Team",
    packages=find_packages(),
    install_requires=[
        "fastapi>=0.95.0",
        "uvicorn>=0.21.0",
        "prometheus-client>=0.16.0",
        "pydantic>=2.0.0",
        "pydantic-settings>=2.0.0",
    ],
    python_requires=">=3.8",
)