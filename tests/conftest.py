# content of conftest.py

from pathlib import Path

test_datafiles = (
    'sample/datafiles/2311.xlsx',
    'sample/datafiles/ma030000.csv',
    'sample/datafiles/katsushika_tourism.csv',
    'sample/datafiles/shimabara_tourism.csv',
    'templates/xxxxxx_tourism.csv',
    'sample/taskfiles/task1.json',
    'sample/taskfiles/task2.json',
)

test_generated_files = (
    'ma030000_clean.csv',
    'hoge.csv',
    'hachijo_2.csv',
    'hachijo_sightseeing_utf8.csv',
    'tourism.csv',
)


def pytest_configure(config):
    """
    Allows plugins and conftest files to perform initial configuration.
    This hook is called for every plugin and initial conftest
    file after command line options have been parsed.
    """
    for path in test_datafiles:
        link_to = Path(path)
        link_from = Path(link_to.name)
        try:
            link_from.symlink_to(link_to)
        except FileExistsError:
            pass


def pytest_sessionstart(session):
    """
    Called after the Session object has been created and
    before performing collection and entering the run test loop.
    """


def pytest_sessionfinish(session, exitstatus):
    """
    Called after whole test run finished, right before
    returning the exit status to the system.
    """


def pytest_unconfigure(config):
    """
    called before test process is exited.
    """
    for path in test_datafiles:
        link_to = Path(path)
        link_from = Path(link_to.name)
        link_from.unlink()

    for path in test_generated_files:
        try:
            Path(path).unlink()
        except FileNotFoundError:
            pass
