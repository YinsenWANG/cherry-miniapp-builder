"""UTF-8 output contract for standalone command-line entry points."""

from __future__ import annotations

import sys


def configure_output() -> None:
    """Keep Unicode output readable even with a legacy console/pipe encoding.

    Configure only at CLI entry, so imports leave the caller's streams alone.
    Redirected in-memory streams already accept Unicode and need no change.
    """
    for stream, errors in ((sys.stdout, "strict"), (sys.stderr, "backslashreplace")):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8", errors=errors)
