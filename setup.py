import pybix
import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="pybix",
    version=pybix.__version__,
    author=pybix.__author__,
    author_email=pybix.__email__,
    description="Python based Zabbix API utility with helper functions ",
    License="MIT",
    keywords=["zabbix", "monitoring", "api"],
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/mattykay/pybix",
    packages=["pybix"],
    classifiers=[
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Natural Language :: English",
        "Topic :: System :: Monitoring",
    ],
)
