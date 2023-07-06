from distutils.core import setup
setup(
  name = 'fast_diff_py',         # How you named your package folder (MyLib)
  packages = ['fast_diff_py'],   # Chose the same as "name"
  version = '0.1.0',      # Start with a small number and increase it with every change you make
  license='MIT',        # Chose a license from here: https://help.github.com/articles/licensing-a-repository
  description = 'Multithreaded implementation of difpy with progress retention.',   # Give a short description about your library
  author = 'Alexander Sotoudeh',                   # Type in your name
  author_email = 'alisot200@gmail.com',      # Type in your E-Mail
  url = 'https://github.com/AliSot2000/Fast-Image-Deduplicator',   # Provide either the link to your github or to your website
  download_url = 'https://github.com/AliSot2000/Fast-Image-Deduplicator/archive/refs/tags/v0.1.0.tar.gz',    # I explain this later on
  keywords = ['python', 'image deduplicator', 'fast image deduplicator'],   # Keywords that define your package best
  install_requires=[            # I get to this in a second
      "matplotlib",
      "numpy",
      "opencv-python",
      "scikit-image",
      "scipy",
      ],
  classifiers=[
      "Development Status :: 4 - Beta",
      'Intended Audience :: Developers',
      "Programming Language :: Python :: 3",
      "Operating System :: MacOS :: MacOS X",
      "Operating System :: Microsoft :: Windows",
      "Operating System :: POSIX :: Linux",
    'License :: OSI Approved :: MIT License',   # Again, pick a license
    'Programming Language :: Python :: 3.8',
  ],
)