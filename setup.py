import setuptools

description = ("Usecase of jupyter notebook widgets "
               "amongst others to visualize time series data.")

with open("requirements.txt") as f:
    requirements = f.read().splitlines()

setuptools.setup(
    name="juts",
    version="2019.1a",
    author="Marcus Riesmeier",
    author_email="marcus.riesmeier@umit.com",
    license="BSD 3-Clause License",
    description=description,
    long_description=description,
    packages=setuptools.find_packages(),
    install_requires=requirements,
    classifiers=(
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: BSD License",
        "Operating System :: OS Independent",
    ),
)

