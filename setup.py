from setuptools import setup, find_packages

setup(
    packages=find_packages(exclude=["tests"]),
    include_package_data=True,
    package_data={
        "idf2yaml": ["iddfiles/*"],
    },
)
