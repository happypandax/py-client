import setuptools

setuptools.setup(
    name='happypandax-client',
    version='1.0.0',
    author="Twiddly",
    author_email="twiddly@pewpew.com"
    description='Client library for communicating with HappyPanda X servers',
    long_description=open('README.md').read(),
    long_description_content_type="text/markdown",
    url='https://github.com/happypandax/py-client',
    license='MIT',
    packages=setuptools.find_packages(),
    include_package_data=True,
    zip_safe=True,
    test_suite='happypandax_client.tests',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Environment :: Other Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Topic :: Software Development :: Libraries'
    ],
)