from setuptools import find_packages, setup

setup(
    name="django-pmc",
    version="0.1.0",
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        "django>=3.2",
        "croniter>=1.0.0",
    ],
)

