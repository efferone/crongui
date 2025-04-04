from setuptools import setup

setup(
    name="crongui",
    version="0.1",
    description="A simple GUI crontab editor",
    author="Your Name",
    author_email="your.email@example.com",
    py_modules=["crongui"],
    install_requires=[],
    entry_points={
        'console_scripts': [
            'crongui=crongui:main',
        ],
    },
)
