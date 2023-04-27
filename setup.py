import setuptools
import os


def read_file(filename):
    with open(os.path.join(os.path.dirname(__file__), filename)) as file:
        return file.read()


description = read_file("Readme.md")

setuptools.setup(
    name="juts",
    version="2023.1",
    author="Marcus Riesmeier",
    author_email="gluehen-sierren-0c@icloud.com",
    license="BSD 3-Clause License",
    description=description.splitlines()[0],
    long_description=description,
    packages=setuptools.find_packages(),
    install_requires=read_file("requirements.txt"),
    classifiers=(
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
    ),
)

