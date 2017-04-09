#!/usr/bin/env python


from setuptools import setup

setup(
        name='hashbot',
        version='1.0',
        description='Bot that finds hashes on Twitter',
        author='Anisse Astier',
        author_email='anisse@astier.eu',
        scripts=['hashbot.py'],
        python_requires='>=2.7,<3.0',
        url='https://github.com/anisse/hashbot',

        install_requires = [
            "requests==2.10.0",
            "requests-oauthlib==0.6.1",
            "argparse==1.2.1",
            "ujson==1.35",
            "configparser==3.5.0",
            ],

        classifiers = [
                "Programming Language :: Python :: 2.7",
            ],

)
