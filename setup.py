from setuptools import setup, find_packages

setup(
    name="aarogya_ai",
    version="1.0.0",
    author="Ashish Rathod",
    # This tells setuptools that all our packages are inside the 'src' directory
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    description="An intelligent API to process and analyze medical lab reports."
)