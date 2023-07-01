from setuptools import setup, find_packages

VERSION = '1.0.0'
DESCRIPTION = 'Fast Image Deduplicator'
LONG_DESCRIPTION = 'Fast Image Deduplicator based on work by Elise Landman.'

# Setting up
setup(
    # the name must match the folder name 'verysimplemodule'
    name="fast_diff_py",
    version=VERSION,
    author="Alexander Sotoudeh",
    author_email="alisot200@gmail.com",
    description=DESCRIPTION,
    long_description=LONG_DESCRIPTION,
    packages=find_packages(),
    install_requires=[
        "matplotlib",
        "numpy",
        "opencv-python",
        "scikit-image",
        "scipy",
    ],

    keywords=['python', 'image deduplicator', 'fast image deduplicator'],
    classifiers=[
        "Development Status :: 4 - Beta"
        "Programming Language :: Python :: 3",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: POSIX :: Linux",
    ]
)