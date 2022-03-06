from setuptools import setup, Extension
import os

base_dir = os.path.dirname(__file__)

with open(os.path.join(base_dir, "README.md")) as f:
    long_description = f.read()

setup(
  name = 'difPy',         
  packages = ['difPy'],   
  version = '2.2',      
  license='MIT',        
  description = 'DifPy Python Duplicate Image Finder - searches for duplicate image files within folders.', 
  long_description=long_description,
  long_description_content_type='text/markdown',
  author = 'Elise Landman',                  
  author_email = 'elisejlandman@hotmail.com', 
  url = 'https://github.com/elisemercury/Duplicate-Image-Finder', 
  download_url = 'https://github.com/elisemercury/Duplicate-Image-Finder/archive/refs/tags/v2.2.tar.gz',    # change everytime for each new release
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