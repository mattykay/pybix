import pybix
from setuptools import setup, find_packages

with open("README.md", "r") as fh:
    long_description = fh.read()

requires = [
    'requests>=2.22.0',
    'docopt>=0.6.2'
]
test_requirements = [
    'pytest-mock',
    'httpretty>=0.9.6',
    'Jinja2>=2.10.1',
    'pytest>=5.0.1'
]

setup(
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
    include_package_data=True,
    python_requires=">=3.6",
    install_requires=requires,
    tests_require=test_requirements,
    zip_safe=False,
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
