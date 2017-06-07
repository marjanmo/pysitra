from setuptools import setup

def readme():
    with open('README.rst') as f:
        return f.read()

setup(name='pysitra',
      version='0.3.3',
      description='Python implementation of the most popular slovenian transformation methods (SiTra!)',
      long_description=readme(),
      url='https://github.com/marjanmo/pysitra',
      author='Marjan Moderc',
      author_email='marjan.moderc@gmail.com',
      license='MIT',
      packages=['pysitra'],
      install_requires=['pandas','geopandas',"numpy","scipy","shapely","click"],
      include_package_data=True,
      entry_points = {'console_scripts': ['sitra=pysitra.sitra_cli:cli']},
      zip_safe=False)