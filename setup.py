import setuptools
import os


def read_file(filename):
    with open(os.path.join(os.path.dirname(__file__), filename)) as file:
        return file.read()


description = read_file("Readme.md")

setuptools.setup(
    name="juts",
    version="2023.4.2",
    url="https://github.com/riemarc/juts",
    author="Marcus Riesmeier",
    author_email="gluehen-sierren-0c@icloud.com",
    license="BSD 3-Clause License",
    description="Jupyter widgets for scheduling processes and visualizing the resulting (live) data",
    long_description_content_type="text/markdown",
    long_description=description,
    packages=setuptools.find_packages(),
    install_requires=read_file("requirements.txt"),
    classifiers=(
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
    ),
)

