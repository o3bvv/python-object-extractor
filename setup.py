#!/usr/bin/env python

from pathlib import Path
from setuptools import setup
from typing import List, Tuple


__here__ = Path(__file__).parent.absolute()


def parse_requirements(file_path: Path) -> Tuple[List[str], List[str]]:
    requirements, dependencies = [], []

    with open(file_path) as f:
        for line in f:
            line = line.strip()

            if not line or line.startswith('#'):
                continue
            if line.startswith("-e"):
                line = line.split(' ', 1)[1]
                dependencies.append(line)
                line = line.split("#egg=", 1)[1]
                requirements.append(line)
            elif line.startswith("-r"):
                name = Path(line.split(' ', 1)[1])
                path = file_path.parent / name
                subrequirements, subdependencies = parse_requirements(path)
                requirements.extend(subrequirements)
                dependencies.extend(subdependencies)
            else:
                requirements.append(line)

    return requirements, dependencies


README = (__here__ / "README.rst").read_text()
REQUIREMENTS, DEPENDENCIES = parse_requirements(__here__ / "requirements.txt")


setup(
    name="python-object-extractor",
    version="1.0.0b1",
    description=(
        "Extract Python object (like class, function, etc) with its "
        "dependencies from local project."
    ),
    license="MIT",
    url="https://github.com/oblalex/python-object-extractor",
    author="Alexander Oblovatnyi",
    author_email="oblovatniy@gmail.com",
    packages=[
        "python_object_extractor",
    ],
    namespace_packages=[],
    include_package_data=True,
    install_requires=REQUIREMENTS,
    dependency_links=DEPENDENCIES,
    classifiers=[
        "Development Status :: 4 - Beta",
        "Programming Language :: Python :: 3.7",
        "License :: OSI Approved :: MIT License",
        "Environment :: Console",
        "Intended Audience :: System Administrators",
        "Intended Audience :: Developers",
        "Natural Language :: English",
        "Topic :: Software Development :: Code Generators",
        "Topic :: Utilities",
    ],
    entry_points={
        'console_scripts': [
            'python-object-extractor=python_object_extractor.main:main',
        ],
    }
)
