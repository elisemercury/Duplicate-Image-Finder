from setuptools import setup

with open("README.md") as f:
    long_description = f.read()

setup(
  name = 'difPy',
  packages = ['difPy'],
  version = '3.0.0',
  license='MIT',
  description = 'difPy Python Duplicate Image Finder - searches for duplicate or similar images within folders.',
  long_description=long_description,
  long_description_content_type='text/markdown',
  author = 'Elise Landman',
  author_email = 'elisejlandman@hotmail.com',
  url = 'https://github.com/elisemercury/Duplicate-Image-Finder',
  download_url = 'https://github.com/elisemercury/Duplicate-Image-Finder/archive/refs/tags/v2.5.0.tar.gz',
  keywords = ['duplicate', 'image', 'finder', "similarity", "pictures"],
  install_requires=[
          'numpy',
          'Pillow',
      ],
  scripts=[
            'bin/difpy'
          ],
  packages=[
             'difPy',
           ],
  classifiers=[
    'Development Status :: 5 - Production/Stable',
    'Intended Audience :: Developers',
    'Topic :: Software Development :: Build Tools',
    'License :: OSI Approved :: MIT License',
    'Programming Language :: Python :: 3.7',
    'Programming Language :: Python :: 3.8',
    'Programming Language :: Python :: 3.9',
  ],
)
