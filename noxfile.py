from __future__ import annotations

import nox

TESTS_PATH = "./tests"


@nox.session(
    python=["3.12"],
    # python=["3.10", "3.11", "3.12"],
    reuse_venv=False,
)
def tests(session: nox.Session):
    session.install(".[test]")

    session.run("pytest", env={"PYTHONPATH": ""})
    # session.run("coverage", "run", "-p", "-m", "pytest", TESTS_PATH, env={'PYTHONPATH': ''})
    # session.run("coverage", "run", "-m", "pytest", TESTS_PATH, env={'PYTHONPATH': ''})
