from setuptools import setup, find_packages
setup(
    name='gpugo',
    version='0.1.1',
    packages=['gpugo'],
    description='Show GPU information and deep learning tasks assignment',
    author='Huiming Sun',
    author_email='sunhuiming55@gmail.com',
    install_requires=[
        'click',
        'pandas',
        'loguru',
    ],

    url='https://github.com/wuchangsheng951/gpugo',
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],

    entry_points='''
        [console_scripts]
        gas=gpugo:main
    ''',
)