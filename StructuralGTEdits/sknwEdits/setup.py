from setuptools import setup

descr = """sknwEdits: skeleton analysis in Python.
Inspired by Juan Nunez-Iglesias's skan.
"""

if __name__ == '__main__':
    setup(name='sknwEdits',
        version='0.1',
        url='https://github.com/AlainKadar/sknwEdits',
        description='Analysis of object skeletons',
        long_description=descr,
        author='AlainKadar',
        author_email='alaink@umich.edu',
        license='BSD 3-clause',
        packages=['sknwEdits'],
        package_data={},
        install_requires=[
            'numpy',
            'igraph'
        ],
    )
