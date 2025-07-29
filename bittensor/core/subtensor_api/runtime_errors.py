from __future__ import annotations


class KonnexRuntimeError(RuntimeError):
    """Base exception for mapped runtime-level chain failures."""


class PopwNotApprovedError(KonnexRuntimeError):
    """Raised when PoPW state does not allow requested action."""


class EscrowStateError(KonnexRuntimeError):
    """Raised when escrow is missing or in invalid state."""


def map_runtime_error(message: str) -> Exception:
    """
    Convert chain error message text into typed SDK exception.

    The matcher intentionally works with plain strings so it can be used for both
    sync and async subtensor responses without extra substrate dependencies.
    """
    text = str(message or "").strip()
    lower_text = text.lower()

    if "popwmodule.notapproved" in lower_text or "popwmodule.invalidstate" in lower_text:
        return PopwNotApprovedError(text or "PoPWModule runtime error")
    if (
        "escrowmodule.invalidescrowstate" in lower_text
        or "escrowmodule.escrownotfound" in lower_text
    ):
        return EscrowStateError(text or "EscrowModule runtime error")
    return KonnexRuntimeError(text or "Unknown runtime error")
