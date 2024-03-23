import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="praw-bot-wrapper",
    version="0.0.8",
    author="mikeacjones",
    author_email="",
    description="A bot wrapper around praw that is intended to make it easier to keep a bot always running even during outages",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/mikeacjones/praw-bot-wrapper",
    packages=setuptools.find_packages(),
    install_requires=["praw>=7.7.1"],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
)
