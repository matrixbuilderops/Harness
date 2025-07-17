from setuptools import setup, find_packages

setup(
    name="mixtral_harness",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "psutil",
        "requests",
        "llama-cpp-python"
    ],
    python_requires=">=3.8",
)