"""
Domain Service — looks up a domain in the Supabase domain_reputation table.
Falls back to a risk heuristic if the domain is not found.

Also runs a separate, REAL pattern analysis directly on the domain string
(TLD, digit/hyphen ratio, length, known-legitimate job-board allowlist).
This requires no database and no external lookup, so it's always genuine,
computed signal — used to avoid showing fabricated DB-style facts (like a
fake "Domain Age: 0 days") for domains that simply aren't in our table yet.
"""

import logging
import re
from typing import List, Tuple

from backend.db.supabase import SupabaseClient
from backend.models.schemas import DomainCheckRequest, DomainCheckResponse

logger = logging.getLogger(__name__)

# TLDs frequently abused for throwaway scam/phishing sites. Not exhaustive —
# absence from this list is not a signal of legitimacy, only presence is a
# signal of elevated risk.
SUSPICIOUS_TLDS = {
    "xyz", "tk", "ml", "ga", "cf", "gq", "top", "work", "click", "loan",
    "win", "bid", "men", "review", "stream", "racing", "download", "icu",
}

# A small allowlist of well-known, legitimate job platforms. This is the
# opposite of a blacklist: it only ever *reduces* suspicion for domains we
# can recognize with high confidence, never increases it for anything else.
KNOWN_JOB_PLATFORMS = {
    "linkedin.com", "naukri.com", "internshala.com", "indeed.com",
    "indeed.co.in", "glassdoor.com", "monster.com", "shine.com",
    "timesjobs.com", "foundit.in", "angel.co", "wellfound.com",
    "ziprecruiter.com", "simplyhired.com",
}


def _analyze_domain_pattern(domain: str) -> Tuple[List[str], float]:
    """Real, rule-based analysis of the domain string itself. No DB, no
    network call — purely computed from the text, so it's always available
    and always genuine (as opposed to a fallback placeholder)."""
    flags: List[str] = []
    score = 0.0
    d = domain.lower().strip()

    if d in KNOWN_JOB_PLATFORMS:
        return (["Recognized as a well-known job platform"], 0.0)

    # Strip to the registrable part for TLD checking.
    parts = d.split(".")
    tld = parts[-1] if len(parts) > 1 else ""
    if tld in SUSPICIOUS_TLDS:
        flags.append(f"Uses a TLD ('.{tld}') commonly abused for throwaway scam sites")
        score += 30

    # Domain names with a high proportion of digits are a classic pattern
    # for mass-registered scam/spam domains (e.g. "quickjobs73891.in").
    core = parts[0] if parts else d
    digits = sum(c.isdigit() for c in core)
    if len(core) > 0 and digits / len(core) > 0.25 and digits >= 3:
        flags.append("Domain name contains an unusually high proportion of digits")
        score += 25

    # Excessive hyphens are another common pattern in throwaway/phishing
    # domains designed to mimic a brand name (e.g. "hr-careers-job-apply.com").
    if core.count("-") >= 2:
        flags.append("Domain name contains multiple hyphens, a common scam-site pattern")
        score += 15

    # Very long subdomain/core names are sometimes used to bury a brand
    # name deep in a long string to look legitimate at a glance.
    if len(core) > 25:
        flags.append("Unusually long domain name")
        score += 10

    if not flags:
        flags.append("No suspicious patterns detected in the domain name itself")

    return (flags, round(min(score, 100), 1))


def _risk_label(score: float) -> str:
    if score <= 25:
        return "LOW RISK"
    if score <= 55:
        return "MEDIUM RISK"
    if score <= 80:
        return "HIGH RISK"
    return "CONFIRMED SCAM"


def _calc_risk(age: int, ssl: bool, trust: float, blacklisted: bool) -> float:
    score = (1 - min(trust, 100) / 100) * 0.50
    score += (0 if ssl else 1) * 0.20
    score += (1 if blacklisted else 0) * 0.20
    score += (1 if age < 90 else 0) * 0.10
    return round(score * 100, 2)


class DomainService:
    def __init__(self, db: SupabaseClient):
        self.db = db

    def check(self, payload: DomainCheckRequest) -> DomainCheckResponse:
        domain = payload.domain_name.lower().strip()
        pattern_flags, pattern_score = _analyze_domain_pattern(domain)

        try:
            settings = __import__("backend.core.config", fromlist=["get_settings"]).get_settings()
            table = settings.supabase_domains_table or "domain_reputation"
            resp = self.db.table(table).select("*").ilike("domain_name", domain).limit(1).execute()
            rows = getattr(resp, "data", []) or []
            if rows:
                r = rows[0]
                age = int(r.get("domain_age_days", 0) or 0)
                ssl = bool(r.get("ssl_valid", False))
                trust = float(r.get("trust_score", 50) or 50)
                blacklisted = bool(r.get("blacklisted", False))
                risk_score = _calc_risk(age, ssl, trust, blacklisted)
                return DomainCheckResponse(
                    domain_name=domain,
                    domain_age_days=age,
                    ssl_valid=ssl,
                    trust_score=trust,
                    blacklisted=blacklisted,
                    risk_score=risk_score,
                    risk_level=_risk_label(risk_score),
                    found=True,
                    pattern_flags=pattern_flags,
                    pattern_score=pattern_score,
                )
        except Exception as e:
            logger.warning("Domain DB lookup failed: %s", e)

        # Not found in domain_reputation — we deliberately do NOT invent
        # age/SSL/trust-score facts here. The risk_score below blends a
        # cautious neutral prior with the real pattern_score so an unknown
        # domain with obvious scam patterns still scores higher than one
        # that looks unremarkable, without claiming to know facts we don't.
        risk_score = round(min(40.0 + pattern_score * 0.6, 100.0), 1)
        return DomainCheckResponse(
            domain_name=domain,
            domain_age_days=0,
            ssl_valid=False,
            trust_score=50.0,
            blacklisted=False,
            risk_score=risk_score,
            risk_level=_risk_label(risk_score),
            found=False,
            pattern_flags=pattern_flags,
            pattern_score=pattern_score,
        )
