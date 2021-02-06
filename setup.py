from setuptools import setup

setup(
    name="site_monitor",
    version="0.0.1",
    url="https://github.com/alexanderlobov/site_monitor",
    author="Alexander Lobov",
    author_email="tardenoisean@gmail.com",
    license="MIT",
    packages=["site_monitor"],
    python_requires=">=3.7",
    install_requires=[
        "aiodns",
        "aiohttp",
        "asyncio",
        "cchardet",
        "kafka-python",
        "psycopg2-binary",
    ]
)
