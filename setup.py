import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="PyTransportNSWv2",
    version="0.2.3",
    author="andystewart999",
    description="Get detailed per-trip transport information from TransportNSW",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/andystewart999/TransportNSW",
    packages=setuptools.find_packages(),
    install_requires=[
        'gtfs-realtime-bindings',
    ],
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
)
