'''
Created on 01.11.2020

@author: joerg
'''
import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="pytedee", # Replace with your own username
    package_dir = {'': 'pytedee'},
    packages = ['pytedee'],
    version="0.0.1",
    author="Jörg Wolff",
    author_email="joerg.wolff@gmx.de",
    description="A Tedee Lock Client package",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/joerg65/pytedee",
    #packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    python_requires='>=3.6',
)