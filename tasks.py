import io
import os
import re
import sys
from glob import glob

from invoke import task

DOCS_PORT = os.environ.get("DOCS_PORT", 8000)
#: branch prefixes for which some checks are skipped
SPECIAL_BRANCHES = ("master", "develop", "release")


@task
def clean(c):
    """ Remove artifacts and binary files. """
    c.run("python setup.py clean --all")
    patterns = ["build", "dist"]
    patterns.extend(glob("*.egg*"))
    patterns.extend(("docs/_build", "**/*.pyc"))
    for pattern in patterns:
        c.run(f"rm -rf {pattern}")


@task
def lint(c):
    """ Run linting tox environments. """
    c.run("tox -epep8,isort,black,pypi-description")


@task  # NOQA
def format(c):  # NOQA
    """ Run code formatting tasks. """
    c.run("tox -eblacken,isort_format")


@task
def towncrier_check(c):    # NOQA
    """ Check towncrier files. """
    output = io.StringIO()
    c.run("git branch --contains HEAD", out_stream=output)
    skipped_branch_prefix = ["pull/", "develop", "master", "HEAD"]
    # cleanup branch names by removing PR-only names in local, remote and disconnected branches to ensure the current
    # (i.e. user defined) branch name is used
    branches = list(
        filter(
            lambda x: x and all(not x.startswith(part) for part in skipped_branch_prefix),
            (
                branch.replace("origin/", "").replace("remotes/", "").strip("* (")
                for branch in output.getvalue().split("\n")
            ),
        )
    )
    print("Candidate branches", ", ".join(output.getvalue().split("\n")))
    if not branches:
        # if no branch name matches, we are in one of the excluded branches above, so we just exit
        print("Skip check, branch excluded by configuration")
        return
    branch = branches[0]
    towncrier_file = None
    for branch in branches:
        if any(branch.startswith(prefix) for prefix in SPECIAL_BRANCHES):
            sys.exit(0)
        try:
            parts = re.search(r"(?P<type>\w+)/\D*(?P<number>\d+)\D*", branch).groups()
            towncrier_file = os.path.join("changes", "{1}.{0}".format(*parts))
            if (
                os.path.exists(towncrier_file)
                and os.path.getsize(towncrier_file) != 0
            ):
                break
            print(
                f"=========================\nCurrent tree does not contain the towncrier file {towncrier_file} or file is empty\nplease check CONTRIBUTING documentation.\n========================="
            )

            sys.exit(2)
        except AttributeError:
            pass
    if not towncrier_file:
        print(
            f"=========================\nBranch {branch} does not respect the '<type>/(<optional-task-type>-)<number>-description' format\n=========================\n"
        )

        sys.exit(1)


@task
def test(c):
    """ Run test in local environment. """
    c.run("python setup.py test")


@task
def test_all(c):
    """ Run all tox environments. """
    c.run("tox")


@task
def coverage(c):
    """ Run test with coverage in local environment. """
    c.run("coverage erase")
    c.run("run setup.py test")
    c.run("report -m")


@task
def tag_release(c, level):
    """ Tag release version. """
    c.run(f"bumpversion --list {level} --no-tag")


@task
def tag_dev(c, level="patch"):
    """ Tag development version. """
    c.run("bumpversion --list %s --message='Bump develop version [ci skip]' --no-tag" % level)


@task(pre=[clean])
def docbuild(c):
    """ Build documentation. """
    os.chdir("docs")
    build_dir = os.environ.get("BUILD_DIR", "_build/html")
    c.run(f"python -msphinx -W -b html -d _build/doctrees . {build_dir}")


@task(docbuild)
def docserve(c):
    """ Serve docs at http://localhost:$DOCS_PORT/ (default port is 8000). """
    from livereload import Server

    server = Server()
    server.watch("docs/conf.py", lambda: docbuild(c))
    server.watch("CONTRIBUTING.rst", lambda: docbuild(c))
    server.watch("docs/*.rst", lambda: docbuild(c))
    server.serve(port=DOCS_PORT, root="_build/html")
