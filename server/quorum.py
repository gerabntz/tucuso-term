"""Deterministic moderation quorum (M1, M3) — adapted from C2C resolve().

A pending item publishes on QUORUM distinct human approvals and zero vetoes.
Any veto rejects. No LLM, no scoring, no reputation — ever (N2, M4).
"""

QUORUM = 2

PENDING = "pending_review"
PUBLISHED = "published"
REJECTED = "rejected"


def resolve(verdicts):
    """verdicts: iterable of (reviewer_id, verdict) with verdict in {'approve','veto'}.

    Distinctness of reviewers is also enforced at the DB layer
    (UNIQUE(reviewer_id, target_type, target_id)); this function re-checks
    so the rule holds even against a corrupted table.
    """
    approvers = set()
    for reviewer_id, verdict in verdicts:
        if verdict == "veto":
            return REJECTED
        if verdict == "approve":
            approvers.add(reviewer_id)
        else:
            raise ValueError(f"unknown verdict: {verdict!r}")
    if len(approvers) >= QUORUM:
        return PUBLISHED
    return PENDING
