import setuptools

description = ("Usecase of JUpyter notebook widgets"
               "amongst others to visualize Time Series data.")

with open('requirements.txt') as f:
    requirements = f.read().splitlines()

setuptools.setup(
    name="juts",
    version="0.1",
    author="Marcus Riesmeier",
    author_email="marcus.riesmeier@umit.com",
    description=description,
    long_description=description,
    packages=setuptools.find_packages(),
    install_requires=requirements,
    classifiers=(
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ),
)

