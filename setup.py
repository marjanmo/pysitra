from setuptools import setup

def readme():
    with open('README.rst') as f:
        return f.read()

setup(name='pysitra',
      version='0.1',
      description='Python implementation of some popular slovenian transformation methods (SiTra!)',
      long_description=readme(),
      url='https://github.com/marjanmo/pysitra',
      author='Marjan Moderc',
      author_email='marjan.moderc@gov.si',
      license='MIT',
      packages=['pysitra'],
      install_requires=['geopandas',"numpy","scipy","shapely","click"],
      include_package_data=True,
      entry_points = {'console_scripts': ['sitra=pysitra.pysitra:cli']},
      zip_safe=False)