# -*- coding: utf-8 -*-
"""
  _   _ _____ _     _____ _____
 | | | |  ___| |   |  ___/  ___|
 | | | | |__ | |   | |__ \ `--.
 | | | |  __|| |   |  __| `--. \
 \ \_/ / |___| |___| |___/\__/ /
  \___/\____/\_____|____/\____/

Created on Apr 25, 2013

.. container:: flexbox

   .. image:: _static/veles_big.png
      :class: left

   .. container::

      %s

███████████████████████████████████████████████████████████████████████████████

Licensed to the Apache Software Foundation (ASF) under one
or more contributor license agreements.  See the NOTICE file
distributed with this work for additional information
regarding copyright ownership.  The ASF licenses this file
to you under the Apache License, Version 2.0 (the
"License"); you may not use this file except in compliance
with the License.  You may obtain a copy of the License at

  http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing,
software distributed under the License is distributed on an
"AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
KIND, either express or implied.  See the License for the
specific language governing permissions and limitations
under the License.

███████████████████████████████████████████████████████████████████████████████
"""


from email.utils import parsedate_tz, mktime_tz, formatdate
from sys import version_info, modules, stdin
from types import ModuleType
from warnings import warn
from veles.paths import __root__

__project__ = "Veles Machine Learning Platform"
__versioninfo__ = 0, 8, 0
__version__ = ".".join(map(str, __versioninfo__))
__license__ = "Samsung Proprietary License"
__copyright__ = u"© 2013 Samsung Electronics Co., Ltd."
__authors__ = ["Gennady Kuznetsov", "Vadim Markovtsev", "Alexey Kazantsev",
               "Lyubov Podoynitsina", "Denis Seresov", "Dmitry Senin",
               "Alexey Golovizin", "Egor Bulychev", "Ernesto Sanches"]
__contact__ = "Gennady Kuznetsov <g.kuznetsov@samsung.com>"

try:
    __git__ = "$Commit$"
    __date__ = mktime_tz(parsedate_tz("$Date$"))
except Exception as ex:
    warn("Cannot expand variables generated by Git, setting them to None")
    __git__ = None
    __date__ = None

__logo__ = \
    r" _   _ _____ _     _____ _____  " "\n" \
    r"| | | |  ___| |   |  ___/  ___| " + \
    (" Version %s" % __version__) + \
    (" %s\n" % formatdate(__date__, True)) + \
    r"| | | | |__ | |   | |__ \ `--.  " + \
    (" Copyright %s\n" % __copyright__) + \
    r"| | | |  __|| |   |  __| `--. \ " \
    " All rights reserved. Any unauthorized use of\n" \
    r"\ \_/ / |___| |___| |___/\__/ / " \
    " this software is strictly prohibited and is\n" \
    r" \___/\____/\_____|____/\____/  " \
    " a subject of your country's laws.\n"

if "sphinx" in modules:
    __doc__ %= "| %s\n      | Version %s %s\n      | %s\n\n      Authors:" \
        "\n\n      * %s" % (__project__, __version__,
                            formatdate(__date__, True), __copyright__,
                            "\n      * ".join(__authors__))
else:
    __doc__ = __logo__.replace(" ", "_", 2)  # nopep8

if version_info.major == 3 and version_info.minor == 4 and \
   version_info.micro < 1:
    warn("Python 3.4.0 has a bug which is critical to Veles OpenCL subsystem ("
         "see issue #21435). It is recommended to upgrade to 3.4.1.")

__plugins__ = set()


def __html__():
    """
    Opens VELES html documentation in the default web browser and builds it,
    if it does not exist.
    """
    import os
    from veles.config import root
    from veles.portable import show_file

    page = os.path.join(root.common.help_dir, "index.html")
    if not os.path.exists(page):
        from runpy import run_path
        print("Building the documentation...")
        run_path(os.path.join(__root__, "docs/generate_docs.py"))
    if os.path.exists(page):
        show_file(page)


class VelesModule(ModuleType):
    """Redefined module class with added properties which are lazily evaluated.
    """

    def __init__(self, *args, **kwargs):
        super(VelesModule, self).__init__(__name__, *args, **kwargs)
        self.__dict__.update(modules[__name__].__dict__)
        self.__units_cache__ = None
        self.__modules_cache_ = None

    def __call__(self, workflow, config=None, **kwargs):
        """
        Launcher the specified workflow and returns the corresponding
        :class:`veles.launcher.Launcher` instance.
        If there exists a standard input, returns immediately after the
        workflow is initialized; otherwise, blocks until it finishes.
        If this command runs under IPython, it's local variables are passed
        into the workflow's :meth:`__init__()`.

        Arguments:
            workflow: path to the Python file with workflow definition.
            config: path to the workflow configuration. If None, *_config.py
                    is taken.
            kwargs: arguments to be passed as if "veles" is executed from the
                    command line. They match the command line arguments except
                    that "-" must be substituted with "_". For example,
                    "backend" -> "--backend", random_seed -> "--random-seed".
                    See "veles --help" for the complete list.
        """
        # FIXME(v.markovtsev): disable R0401 locally when pylint issue is fixed
        # https://bitbucket.org/logilab/pylint/issue/61
        # from veles.__main__ import Main  # pylint: disable=R0401
        Main = __import__("veles.__main__").__main__.Main
        if config is None:
            config = "-"
        main = Main(stdin.isatty(), workflow, config, **kwargs)
        main.run()
        return main.launcher

    def __scan(self):
        import os
        import sys

        blacklist = {"tests", "external", "libVeles", "libZnicz"}
        # Temporarily disable standard output since some modules produce spam
        # during import
        stdout = sys.stdout
        sys.stdout = open(os.devnull, 'w')
        for root, dirs, files in os.walk(os.path.dirname(self.__file__)):
            if any(b in root for b in blacklist):
                del dirs[:]
                continue
            for file in files:
                modname, ext = os.path.splitext(file)
                if ext != '.py':
                    continue
                modpath = os.path.relpath(root, self.__root__).replace(
                    os.path.sep, '.')
                try:
                    yield __import__("%s.%s" % (modpath, modname))
                except Exception as e:
                    stdout.write("%s: %s\n" % (
                        os.path.relpath(os.path.join(root, file),
                                        self.__root__),
                        e))
        sys.stdout.close()
        sys.stdout = stdout

    @property
    def __units__(self):
        """
        Returns the array with all Unit classes found in the package file tree.
        """
        if self.__units_cache__ is not None:
            return self.__units_cache__

        for _ in self.__scan():
            pass

        from veles.unit_registry import UnitRegistry
        self.__units_cache__ = UnitRegistry.units
        return self.__units_cache__

    @property
    def __modules__(self):
        if self.__modules_cache_ is None:
            self.__modules_cache_ = set(self.__scan())
        return self.__modules_cache_

    @property
    def __loc__(self):
        """Calculation of lines of code relies on "cloc" utility.
        """
        from subprocess import Popen, PIPE

        result = {}

        def calc(cond, exclude_docs=True):
            cmd = ("cd %s && echo $(find %s ! -path '*debian*' "
                   "%s ! -path '*.pybuild*' "
                   "-exec cloc --quiet --csv {} \; | "
                   "sed -n '1p;0~3p' | tail -n +2 | cut -d ',' -f 5 | "
                   "tr '\n' '+' | head -c -1) | bc") %\
                  (self.__root__, cond,
                   "! -path '*docs*'" if exclude_docs else "")
            discovery = Popen(cmd, shell=True, stdout=PIPE)
            num, _ = discovery.communicate()
            return int(num)
        result["core"] = \
            calc("-name '*.py' ! -path '*cpplint*' ! -path './deploy/*' "
                 "! -path './web/*' ! -path './veles/external/*' "
                 "! -name create-emitter-tests.py ! -path "
                 "'./veles/tests/*' ! -path './veles/znicz/tests/*'")
        result["core"] += calc("veles/external/txzmq  -name '*.py'")
        result["tests"] = calc("'./veles/tests' './veles/znicz/tests' "
                               "-name '*.py'")
        result["c/c++"] = calc(
            "\( -name '*.cc' -o -name '*.h' -o -name '*.c' \) ! -path "
            "'*google*' ! -path '*web*' ! -path '*zlib*' !"
            " -path '*libarchive*' ! -path '*yaml-cpp*'")
        result["js"] = calc("-name '*.js' ! -path '*.min.js*' "
                            "! -path '*viz.js*' ! -path '*emscripten*'")
        result["docs"] = calc("-name '*manualrst*'", False)
        result["opencl"] = calc("-name '*.cl' ! -path './web/*'")
        result["java"] = calc("'./mastodon/lib/src/main' -name '*.java'")
        result["tests"] += calc("'./mastodon/lib/src/test' -name '*.java'")

        result["all"] = sum(result.values())
        return result


if not isinstance(modules[__name__], VelesModule):
    modules[__name__] = VelesModule()

if __name__ == "__main__":
    __html__()
