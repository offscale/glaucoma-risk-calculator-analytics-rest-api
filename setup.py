# -*- coding: utf-8 -*-

"""
setup.py implementation, interesting because it parsed the first __init__.py and
    extracts the `__author__` and `__version__`
"""

from ast import parse
from distutils.sysconfig import get_python_lib
from functools import partial
from os import listdir, path

from setuptools import find_packages, setup

package_name = "glaucoma_risk_calculator_analytics_rest_api"


def to_funcs(*paths):
    """
    Produce function tuples that produce the local and install dir, respectively.

    :param paths: one or more str, referring to relative folder names
    :type paths: ```*paths```

    :returns: 2 functions
    :rtype: ```Tuple[Callable[Optional[List[str]], str], Callable[Optional[List[str]], str]]```
    """
    return (
        partial(path.join, path.dirname(__file__), package_name, *paths),
        partial(path.join, get_python_lib(prefix=""), package_name, *paths),
    )


if __name__ == "__main__":
    with open(path.join(package_name, "__init__.py")) as f:
        __author__, __version__ = map(
            lambda const: const.value if version_info > (3, 6) else const.s,
            map(
                attrgetter("value"),
                map(
                    itemgetter(0),
                    map(
                        attrgetter("body"),
                        map(
                            parse,
                            filter(
                                lambda line: line.startswith("__version__")
                                or line.startswith("__author__"),
                                f,
                            ),
                        ),
                    ),
                ),
            ),
        )

    _data_join, _data_install_dir = to_funcs("_data")

    setup(
        name=package_name,
        author=__author__,
        version=__version__,
        install_requires=["pyyaml"],
        test_suite=package_name + ".tests",
        packages=find_packages(),
        package_dir={package_name: package_name},
        classifiers=[
            "Development Status :: 3 - Alpha",
            "Environment :: Console",
            "Intended Audience :: Developers",
            "License :: OSI Approved",
            "License :: OSI Approved :: Apache Software License",
            "License :: OSI Approved :: MIT License",
            "Natural Language :: English",
            "Operating System :: OS Independent",
            "Programming Language :: Python :: 2.7",
            "Programming Language :: Python :: 3",
            "Topic :: Internet :: WWW/HTTP :: HTTP Servers",
        ],
        data_files=[
            (_data_install_dir(), list(map(_data_join, listdir(_data_join())))),
        ],
    )
