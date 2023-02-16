from setuptools import setup
import os

base_dir = os.path.dirname(__file__)

try:
  with open(os.path.join(base_dir, "README_pypi.md")) as f:
    long_description = f.read()
except:
  with open(os.path.join(base_dir, "README.md")) as f:
    long_description = f.read()

setup(
  name = 'difPy',         
  packages = ['difPy'],   
  version = '3.0.0.1',      
  license='MIT',        
  description = 'difPy Python Duplicate Image Finder - searches for duplicate or similar images within folders.', 
  long_description=long_description,
  long_description_content_type='text/markdown',
  author = 'Elise Landman',                  
  author_email = 'elisejlandman@hotmail.com', 
  url = 'https://github.com/elisemercury/Duplicate-Image-Finder', 
  download_url = 'https://github.com/elisemercury/Duplicate-Image-Finder/archive/refs/tags/v3.0.0.tar.gz',    # change everytime for each new release
  keywords = ['duplicate', 'image', 'finder', "similarity", "pictures"],  
  install_requires=[          
          'scikit-image',
          'matplotlib',
          'numpy',
          'opencv-python',
      ],
  classifiers=[
    'Development Status :: 5 - Production/Stable',      # Chose either "3 - Alpha", "4 - Beta" or "5 - Production/Stable" as the current state of your package
    'Intended Audience :: Developers',      
    'Topic :: Software Development :: Build Tools',
    'License :: OSI Approved :: MIT License',    
    'Programming Language :: Python :: 3.7',
    'Programming Language :: Python :: 3.8', #Specify which pyhton versions to support
    'Programming Language :: Python :: 3.9',
  ],
)