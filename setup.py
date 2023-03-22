from setuptools import setup, find_packages

with open("requirements.txt") as f:
	install_requires = f.read().strip().split("\n")

# get version from __version__ variable in flowwolf_process_flow/__init__.py
from flowwolf_process_flow import __version__ as version

setup(
	name="flowwolf_process_flow",
	version=version,
	description="Processing Framework",
	author="Flowwolf Inc.",
	author_email="dev@flowwolf.io",
	packages=find_packages(),
	zip_safe=False,
	include_package_data=True,
	install_requires=install_requires
)
