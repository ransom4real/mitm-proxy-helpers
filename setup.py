''' Setup for package '''
from setuptools import setup, find_packages

setup(
    name='mitm-proxy-helpers',
    version='0.0.1',
    description="MITM Proxy Helpers for Direct/Transparent proxy manipulation",
    long_description=""" """,
    author='Ransom Voke Anighoro',
    author_email='voke.anighoro@gmail.com',
    url='https://github.com/ransom4real/mitm-proxy-helpers',
    license='MIT',
    packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
    include_package_data=True,
    zip_safe=True,
    install_requires=[
        "paramiko"
    ],
    keywords=['MITM', 'proxy', 'helpers'],
    classifiers=[
        'Development Status :: 5 - Production/Stable',
        'Intended Audience :: Developers',
        'Topic :: Software Development :: Build Tools',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
    ],
)
