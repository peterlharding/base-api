"""Every Makefile target that drives a script must pass $(ARGS) through.

`make prune ARGS=--dry-run` was a real prune: make accepts a variable the
recipe never mentions and says nothing, so the flag was silently dropped
and a request to report became a request to delete.  Nothing about the
output distinguished the two until it had already run.

The guard is a pattern rather than a review because the failure is silent
by construction - a new target written without $(ARGS) works perfectly
until someone passes a flag to it.
"""

import re

from pathlib import Path


MAKEFILE = Path(__file__).resolve().parents[1] / "Makefile"

# A recipe line is tab-indented; these are the ones that hand control to a
# script in scripts/, which is where argparse can vet what it is given.
_RECIPE = re.compile(r"^\t.*\bscripts/\w+\.py\b.*$", re.MULTILINE)


def _script_recipes():
    return _RECIPE.findall(MAKEFILE.read_text())


def test_the_makefile_drives_scripts():
    """Guard the guard: a rename that empties the match set proves nothing."""
    assert len(_script_recipes()) >= 5


def test_script_targets_pass_args_through():
    without = [line.strip() for line in _script_recipes() if "$(ARGS)" not in line]

    assert not without, (
        "these Makefile recipes drop a flag passed as ARGS= instead of "
        f"failing on it: {without}"
    )
