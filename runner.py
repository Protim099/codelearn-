"""Pluggable code-runner interface.

IMPORTANT: user code must NEVER be executed inside the Django process or on the web server.
The default `DemoRunner` does not execute anything and says so clearly.

To integrate a real sandbox later (e.g. a Judge0 instance, a container-per-run worker, Firecracker, etc.):
  1. Subclass BaseRunner and implement run() by calling the external, isolated service.
  2. Set CODE_RUNNER=your.module.YourRunner in .env.
"""
from dataclasses import dataclass, field

from django.conf import settings
from django.utils.module_loading import import_string


@dataclass
class RunResult:
    status: str                      # 'demo' | 'passed' | 'failed' | 'error'
    output: str = ""
    details: list = field(default_factory=list)   # per-test-case results when a real runner is used


class BaseRunner:
    def run(self, code: str, language: str, test_cases: list) -> RunResult:
        raise NotImplementedError


class DemoRunner(BaseRunner):
    """Saves the submission only. It does NOT run the code or compare any output."""

    def run(self, code, language, test_cases):
        return RunResult(
            status="demo",
            output=("DEMO MODE: no code execution engine is configured, so your code was saved but NOT executed. "
                    f"{len(test_cases)} test case(s) were not evaluated."),
        )


def get_runner() -> BaseRunner:
    return import_string(settings.CODE_RUNNER)()
