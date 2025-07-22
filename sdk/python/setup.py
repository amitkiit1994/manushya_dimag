from setuptools import setup, find_packages

setup(
    name="manushya_sdk",
    version="0.1.0",
    description="Python SDK for Manushya.ai API",
    author="Manushya.ai",
    packages=find_packages(),
    install_requires=[
        "httpx>=0.24.0",
        "pydantic>=2.0.0",
        "attrs>=22.0.0"
    ],
    python_requires=">=3.8",
) 