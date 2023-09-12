import os
from setuptools import setup

def read(fname):
    return open(os.path.join(os.path.dirname(__file__), fname)).read()

setup(
    name = "reportgenerator",
    version = "0.1.0",
    python_requires='>=3.11.0',
    include_package_data=True,
    author = "Gregor Lohaus",
    author_email = "lohausgregor@gmail.com",
    license = "BSD",
    packages=['reportgenerator'],
    install_requires=['jinja2','teamleaderclient'],
    entry_points = {
        'console_scripts': ['reportgenerator=reportgenerator.reportgenerator:main'],
    },
    long_description=read('README'),
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Topic :: Utilities",
        "License :: OSI Approved :: BSD License",
    ],
)