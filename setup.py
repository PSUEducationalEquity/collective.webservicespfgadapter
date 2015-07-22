from setuptools import setup, find_packages
import os

version = '1.0'

setup(name='collective.webservicespfgadapter',
      version=version,
      description="PloneFormGen adapter that sends the form submission \
          to a web service",
      long_description=open("README.txt").read() + "\n" +
                       open("CHANGES.txt").read(),
      # Get more strings from
      # http://pypi.python.org/pypi?%3Aaction=list_classifiers
      classifiers=[
        "Framework :: Plone",
        "Programming Language :: Python",
        ],
      keywords='Zope CMF Plone Web Service PloneFormGen forms integration',
      author='Paul Rentschler',
      author_email='par117@psu.edu',
      url='',
      license='GPL',
      packages=find_packages(exclude=['ez_setup']),
      namespace_packages=['collective'],
      include_package_data=True,
      zip_safe=False,
      install_requires=[
          'setuptools',
          'Products.PloneFormGen>=1.7.0',
          'Products.TALESField',
      ],
      entry_points="""
      # -*- Entry points: -*-
      [z3c.autoinclude.plugin]
      target = plone
      """,
      )

