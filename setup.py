from setuptools import setup
from glaucoma_analytics_rest_api import __version__

if __name__ == '__main__':
    setup(name='glaucoma_analytics_rest_api', version=__version__,
          author='Samuel Marks', license='MIT', py_modules=['glaucoma_analytics_rest_api'],
          test_suite='tests')
