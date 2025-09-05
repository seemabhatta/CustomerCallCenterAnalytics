from setuptools import setup, find_packages

setup(
    name="customer-call-center-analytics",
    version="0.1.0",
    description="AI Co-Pilot for Customer Call Center Analytics",
    author="Your Name",
    packages=find_packages(),
    install_requires=[
        "openai>=1.52.0",
        "tinydb>=4.8.0",
        "click>=8.0.0",
        "python-dotenv>=1.0.0",
        "pydantic>=2.0.0",
    ],
    entry_points={
        "console_scripts": [
            "call-center-cli=src.cli.main:cli",
        ],
    },
)
