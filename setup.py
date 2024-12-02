from setuptools import setup, find_packages

setup(
    name="virtualinfluencer",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        "fastapi",
        "uvicorn",
        "pydantic",
        "psutil",
    ],
)
