from os.path import dirname, join

from setuptools import setup

import pp_role_mining


def read_file(filename):
    with open(join(dirname(__file__), filename)) as f:
        return f.read()


setup(
    name=pp_role_mining.__name__,
    version=pp_role_mining.__version__,
    description=pp_role_mining.__doc__.strip(),
    long_description=read_file('README.md'),
    author=pp_role_mining.__author__,
    author_email=pp_role_mining.__author_email__,
    py_modules=[pp_role_mining.__name__],
    include_package_data=True,
    packages=['pp_role_mining'],
    url='https://github.com/m4jidRafiei/privacyAware-ConnectorMethod_DFG',
    license='GPL 3.0',
    install_requires=[
        'pm4py',
        'distributed==1.21.8',
        'pycrypto==2.6.1',
        'p_privacy_metadata==0.0.1',
        'networkx==2.3',
        'matplotlib==2.2.2',
        'pyvis==0.1.4.1'
    ],
    project_urls={
        'Source': 'https://github.com/m4jidRafiei/privacyAware-roleMining'
    }
)
