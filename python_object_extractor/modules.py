import os
import sys

from distutils import sysconfig
from importlib import import_module
from types import ModuleType
from typing import Optional

from pip._internal.commands.show import search_packages_info
from pip._internal.utils.misc import get_installed_distributions
from pip._vendor.pkg_resources import Requirement


PYTHON_ROOT_DIR = sysconfig.get_python_lib(standard_lib=True)
THIRD_PARTY_PACKAGES_ROOT_DIR = sysconfig.get_python_lib(standard_lib=False)


def get_module_by_name(module_name: str) -> ModuleType:
    module = sys.modules.get(module_name)

    if module is None:
        module = import_module(module_name)

    return module


def is_builtin_module(module: ModuleType) -> bool:
    return module.__name__ in sys.builtin_module_names


def is_stdlib_module(module: ModuleType) -> bool:
    return (
           is_builtin_module(module)
        or os.path.realpath(module.__file__).startswith(PYTHON_ROOT_DIR)
    )


def is_third_party_module(module: ModuleType) -> bool:
    return (
        os
        .path
        .realpath(module.__file__)
        .startswith(THIRD_PARTY_PACKAGES_ROOT_DIR)
    )


def is_project_module(module: ModuleType, project_path: str) -> bool:
    return os.path.realpath(module.__file__).startswith(project_path)


def get_module_requirement(module: ModuleType) -> Optional[Requirement]:
    module_relative_location = os.path.relpath(
        module.__file__,
        THIRD_PARTY_PACKAGES_ROOT_DIR,
    )

    for distribution_info in get_installed_distributions():
        key = distribution_info.project_name

        package_info = list(search_packages_info([key]))[0]
        package_files = package_info['files']
        package_sources = {
            x
            for x in package_files
            if x.endswith('.py')
        }

        if module_relative_location in package_sources:
            return distribution_info.as_requirement()
