from setuptools import setup, find_packages

setup(
    name="deep-research-engine",
    version="0.1.0",
    packages=find_packages(where='src'),
    package_dir={'': 'src'},
    install_requires=[
        'groq>=0.1.0',
        'numpy>=1.22.0',
        'requests>=2.28.0',
        'PyYAML>=6.0',
        'logging>=0.5.1.2',
    ],
    extras_require={
        'test': [
            'pytest>=7.3.1',
            'unittest2>=1.1.0',
        ],
    },
    author="Your Name",
    description="A query processing engine for deep research",
    long_description=open('README.md').read(),
    long_description_content_type="text/markdown",
)