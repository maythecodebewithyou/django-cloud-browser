"""Fabric file."""
from __future__ import with_statement
from __future__ import print_function

import os

from contextlib import contextmanager
from fabric.api import local


###############################################################################
# Constants
###############################################################################
MOD = "cloud_browser"
PROJ = "cloud_browser_project"
PROJ_SETTINGS = ".".join((PROJ, "settings"))

DEV_DB_DIR = os.path.join(PROJ, "db")

CHECK_INCLUDES = (
    "fabfile.py",
    "setup.py",
    MOD,
    PROJ,
)
PYLINT_CFG = "dev/pylint.cfg"

DOC_INPUT = "doc"
DOC_OUTPUT = "doc_html"
DOC_UNDERSCORE_DIRS = (
    "sources",
    "static",
)

BUILD_DIRS = (
    "dist",
    "django_cloud_browser.egg-info",
)

SDIST_RST_FILES = (
    "INSTALL.rst",
    "README.rst",
    "CHANGES.rst",
)
SDIST_TXT_FILES = [os.path.splitext(x)[0] + ".txt" for x in SDIST_RST_FILES]


###############################################################################
# Build
###############################################################################
def clean():
    """Clean build files."""
    for build_dir in list(BUILD_DIRS) + [DOC_OUTPUT, DEV_DB_DIR]:
        local("rm -rf %s" % build_dir)


@contextmanager
def _dist_wrapper():
    """Add temporary distribution build files (and then clean up)."""
    try:
        # Copy select *.rst files to *.txt for build.
        for rst_file, txt_file in zip(SDIST_RST_FILES, SDIST_TXT_FILES):
            local("cp %s %s" % (rst_file, txt_file))

        # Perform action.
        yield
    finally:
        # Clean up temp *.txt files.
        for rst_file in SDIST_TXT_FILES:
            local("rm -f %s" % rst_file, capture=False)


def sdist():
    """Package into distribution."""
    with _dist_wrapper():
        local("python setup.py sdist", capture=False)


def register():
    """Register and prep user for PyPi upload.

    .. note:: May need to tweak ~/.pypirc file per issue:
        http://stackoverflow.com/questions/1569315
    """
    with _dist_wrapper():
        local("python setup.py register", capture=False)


def upload():
    """Upload package."""
    with _dist_wrapper():
        local("python setup.py sdist upload", capture=False)


###############################################################################
# Quality
###############################################################################
def pylint(rcfile=PYLINT_CFG):
    """Run pylint style checker.

    :param rcfile: PyLint configuration file.
    """
    # Have a spurious DeprecationWarning in pylint.
    local("pylint --rcfile=%s %s" %
          (rcfile, " ".join(CHECK_INCLUDES)), capture=False)


def check():
    """Run all checkers."""
    # TODO: Add pycodestyle.
    # https://github.com/ryan-roemer/django-cloud-browser/issues/15
    pylint()


###############################################################################
# Documentation
###############################################################################
def _parse_bool(value):
    """Convert ``string`` or ``bool`` to ``bool``."""
    if isinstance(value, bool):
        return value

    elif isinstance(value, str):
        if value == 'True':
            return True
        elif value == 'False':
            return False

    raise Exception("Value %s is not boolean." % value)


def docs(output=DOC_OUTPUT, proj_settings=PROJ_SETTINGS, github=False):
    """Generate API documentation (using Sphinx).

    :param output: Output directory.
    :param proj_settings: Django project settings to use.
    :param github: Convert to GitHub-friendly format?
    """

    local("export PYTHONPATH='' && "
          "export DJANGO_SETTINGS_MODULE=%s && "
          "sphinx-build -b html %s %s" % (proj_settings, DOC_INPUT, output),
          capture=False)

    if _parse_bool(github):
        local("touch %s/.nojekyll" % output, capture=False)


###############################################################################
# Django Targets
###############################################################################
def _manage(target, extra='', proj_settings=PROJ_SETTINGS):
    """Generic wrapper for ``django-admin.py``."""
    local("export PYTHONPATH='' && "
          "export DJANGO_SETTINGS_MODULE='%s' && "
          "django-admin.py %s %s" %
          (proj_settings, target, extra),
          capture=False)


def syncdb(proj_settings=PROJ_SETTINGS):
    """Run syncdb."""
    local("mkdir -p %s" % DEV_DB_DIR)
    _manage("syncdb", proj_settings=proj_settings)


def run_server(addr="127.0.0.1:8000", proj_settings=PROJ_SETTINGS):
    """Run Django dev. server."""
    _manage("runserver", addr, proj_settings)
