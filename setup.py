from Cython.Build import cythonize
from setuptools import find_packages, setup, Extension

ext = Extension(name="StructuralGTEdits.convert", sources=["convert.pyx"])

setup(
    name='StructuralGTEdits',
    packages = find_packages(),
    install_requires=[
        'numpy',
        'scipy',
        'scikit-image',
        'matplotlib',
        'networkx',
        'opencv-python',
        'Pillow',
        'pandas',
        'Cython',
        'gsd',
        'python-igraph',
        'pytest',
        'cmake'
    ],
    #ext_modules=(cythonize("convert.pyx")),
    ext_modules=cythonize(ext),
    zip_safe=False,
    package_data={'StructuralGTEdits':['pytest/data/*/*']},
)
