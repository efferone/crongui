from setuptools import setup

setup(
    name="crongui",
    version="0.1.1",
    description="a GUI editor for cron",
    author="Euan Fisher",
    py_modules=["crongui"],
    install_requires=[],
    entry_points={
        'console_scripts': [
            'crongui=crongui:main',
        ],
    },
)
