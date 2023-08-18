from setuptools import setup, find_packages

setup(
    name="defillama-py",
    version="0.1.0",
    description="A Python wrapper for the DeFiLlama API",
    long_description=open("README.md", "r").read(),
    long_description_content_type="text/markdown",
    author="Landon Gingerich",
    author_email="landon.ging@gmail.com",
    url="https://github.com/lgingerich/defillama-py",
    license="MIT",
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
    ],
    keywords="defillama, defi, API, wrapper",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    python_requires=">=3.8, <4",
    install_requires=[
        # Add project dependencies
        "requests>=2.31.0",
        "polars>=0.18.15",
    ],
    extras_require={
        "dev": [
            # Add development dependencies
            "pytest>=7.4.0",
        ],
    },
)