#!/usr/bin/env python3

from setuptools import setup, find_packages

long_description = '''
IoT Car Share system
'''

version = "20.0.0"

# requirements installed independently
requirements = []

if __name__ == '__main__':
    setup(
        name='iot_car_share_system',
        version=version,
        versions="20.*",
        description='IoT Car Share System',
        long_description=long_description,
        author="",
        packages=find_packages(exclude=['tests', 'docs'],
                               include=[
                                   'master_pi', 'css_rpc', 'agent_pi',
                                   'bluetooth_services', 'qr_code'
                               ]),
        install_requires=requirements,
        classifiers=[
            'Framework :: Pytest',
            'Intended Audience :: Developers',
        ],
    )
