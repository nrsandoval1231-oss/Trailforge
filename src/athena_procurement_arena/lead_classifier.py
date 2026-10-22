"""Deterministic keyword classifier and score for unreviewed search hits (the Find tab).

Pure functions, no I/O. Nothing here verifies anything: it reports which words matched so an operator can see why a
hit was flagged, and a score that only orders the lists. A date found in a snippet is a literal quote, never a status.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date
from urllib.parse import urlsplit

# Bump when any rule or weight below changes: LeadStore then re-ranks every stored lead (kind, matched, score only).
CLASSIFIER_VERSION = 3


def _compile(pairs):
    return tuple((label, re.compile(pattern, re.IGNORECASE)) for label, pattern in pairs)


def _scan(terms, text: str) -> tuple[str, ...]:
    return tuple(label for label, pattern in terms if pattern.search(text))


RFP_TERMS = _compile((
    ("rfp", r"\brfps?\b"),
    ("request for proposal", r"\brequests? for proposals?\b"),
    ("request for qualifications", r"\brequests? for qualifications?\b"),
    ("request for quotation", r"\brequests? for quot(?:e|ation)s?\b"),
    ("rfq", r"\brfqs?\b"),
    ("solicitation", r"\bsolicitations?\b"),
    ("invitation for bid", r"\binvitations? (?:for|to) bids?\b"),
    ("ifb", r"\bifbs?\b"),
    ("tender", r"\btenders?\b"),
    ("bid notice", r"\bbid (?:notices?|opportunit(?:y|ies))\b"),
    ("request for information", r"\brequests? for information\b"),
    ("rfi", r"\brfis?\b"),
    ("soliciting proposals", r"\b(?:solicit(?:s|ing|ed)?|seek(?:s|ing)?|invit(?:es|ing|ation for)) "
                             r"(?:sealed )?(?:proposals|bids|offers)\b"),
    ("sealed bid", r"\bsealed (?:bids?|proposals?)\b"),
    ("proposals opened", r"\b(?:proposals|bids) (?:will be|are to be|shall be) (?:publicly )?(?:opened|received)\b"),
    ("power procurement", r"\b(?:temporary (?:power|generation)|bridge power|power generation|generators?)\b"
                          r"[^\n]{0,60}?\bprocurement\b"),
))
# Wording that counts as an RFP word only on an official host (an addendum or a /bids/ page there is a solicitation
# document; anywhere else the same words are too generic).
_OFFICIAL_RFP_TERMS = _compile((
    ("addendum", r"\baddend(?:um|a)\b"),
    ("bids page", r"(?<![a-z0-9])bids?(?![a-z0-9])"),
))
_TEMP_POWER = re.compile(r"\b(?:temporary (?:power|generation)|bridge power)\b", re.IGNORECASE)
_PROCUREMENT = re.compile(r"\bprocurement\b", re.IGNORECASE)
PROJECT_TERMS = _compile((
    ("announced", r"\bannounce[sd]?\b"),
    ("planned", r"\b(?:planned|proposed)\b"),
    ("permitting", r"\bpermit(?:s|ting|ted)?\b"),
    ("environmental review", r"\benvironmental (?:review|impact)\b"),
    ("rezoning", r"\brezon(?:e|ed|ing)\b"),
    ("construction", r"\bconstruction\b"),
    ("groundbreaking", r"\bground ?breaking\b"),
    ("expansion", r"\bexpansions?\b"),
    ("data center", r"\bdata ?cent(?:er|re)s?\b"),
    ("hyperscale", r"\bhyperscale\b"),
    ("substation", r"\bsubstations?\b"),
    ("compressor station", r"\bcompressor stations?\b"),
    ("pipeline", r"\bpipelines?\b"),
    ("refinery", r"\brefiner(?:y|ies)\b"),
))
# Project words that name energy infrastructure on their own. The generic ones need energy context, and "permitting"
# alone (permit explainers, home-project pages) never makes a project.
_PROJECT_INHERENT = {"data center", "hyperscale", "substation", "compressor station", "pipeline", "refinery"}
_PROJECT_WEAK = {"permitting"}
# Power words: the _STRONG_POWER ones weigh 10 in the score, the rest 4. `load` alone is deliberately absent (too
# generic); "large load" is the specific form.
POWER_TERMS = _compile((
    ("temporary power", r"\btemporary power\b"),
    ("bridge power", r"\bbridg(?:e|ing) power\b"),
    ("temporary generation", r"\btemporary generation\b"),
    ("power generation", r"\bpower generation\b"),
    ("generator", r"\bgenerators?\b"),
    ("megawatt", r"\bmegawatts?\b"),
    ("MW", r"(?<![a-z])mw(?![a-z])"),
    ("gigawatt", r"\bgigawatts?\b"),
    ("GW", r"\d[\d.,]*\s*-?\s*gw(?![a-z])"),  # needs a number, so "GW Law" is not a size
    ("microgrid", r"\bmicro-?grids?\b"),
    ("substation", r"\bsubstations?\b"),
    ("turbine", r"\bturbines?\b"),
    ("interconnection", r"\binterconnection\b"),
    ("behind-the-meter", r"\bbehind[- ]the[- ]meter\b"),
    ("on-site power", r"\bon-?site (?:power|generation)\b"),
    ("reciprocating engine", r"\breciprocating engines?\b"),
    ("off-grid power", r"\boff-?grid power\b"),
    ("power plant", r"\b(?:power|gas) plants?\b"),
    ("large load", r"\blarge[- ]loads?\b"),
))
_STRONG_POWER = {"temporary power", "bridge power", "temporary generation", "generator", "megawatt", "MW", "gigawatt",
                 "GW"}
_SIZE_TERMS = {"megawatt", "MW", "gigawatt", "GW"}
# Broader energy vocabulary: an RFP-like hit needs one of these (or a POWER term, or an energy/utility host).
# "generation" and "capacity" count only next to a power word (they are common outside energy).
_ENERGY_CONTEXT = re.compile(
    r"\b(?:power|electric(?:al|ity|ic)?|energy|utility|utilities|megawatts?|grid|nuclear|natural gas|lng|solar)\b"
    r"|\b(?:power|electric(?:ity)?|energy) generation\b|\bgeneration (?:of )?(?:power|electric(?:ity)?|energy)\b"
    r"|\b(?:power|electric(?:al|ity)?|megawatt|mw|generating|generation) capacity\b"
    r"|\bcapacity (?:of )?\d[\d,.]* ?(?:mw|megawatts?)\b", re.IGNORECASE)
_HOST_ENERGY = re.compile(r"power|energy|electric|utilit", re.IGNORECASE)
_SPECIFIC_RFP = re.compile(r"\brequests? for proposals?\b", re.IGNORECASE)
_EVENT_VERB = re.compile(r"\b(?:acquire[sd]?|approv(?:es|ed)|clears?|cleared|files?|filed|plans?|breaks? ground|"
                         r"secures?|selected|awarded|invokes?|scoop|signs?|begins?|launch(?:es|ed)?)\b",
                         re.IGNORECASE)
# "Project Description", "Project Manager" and similar document headings are not project names.
_NAMED_PROJECT = re.compile(r"\bProject (?!(?:Description|Manager|Management|Overview|Summary|Details|Information|"
                            r"Team|Plan|Scope|Schedule|Status|Update|Number|Name|Title|Types?|Requirements?|"
                            r"Specifications?|Documents?|Costs?|Budget|Delivery|Controls?)\b)[A-Z][a-z]+")
# Explainer / reference patterns, matched against the title and URL path.
EXPLAINER_TERMS = _compile((
    ("glossary", r"\bglossary\b"),
    ("definition", r"\bdefinitions?\b"),
    ("what is/are", r"\bwhat(?: is|['’]s| are)\b"),
    ("how to", r"\bhow (?:to|does|do)\b"),
    ("guide", r"\bguide\b"),
    ("understanding", r"\bunderstanding\b"),
    ("explained", r"\bexplained\b"),
    ("best practices", r"\bbest practices?\b"),
    ("market report", r"\bmarket (?:size|share|trends?|forecast|report|analysis|intelligence)\b|\bforecasts?\b"),
    ("study", r"\bstudy\b"),
    ("white paper", r"\bwhite ?paper\b"),
    ("template", r"\btemplates?\b"),
    ("faq", r"\bfaqs?\b"),
    ("key parts", r"\bkey (?:parts|facts|takeaways)\b|\b\d+ (?:key )?(?:parts|facts|things|ways)\b"),
    ("benefits, risks", r"\bbenefits,? (?:and )?risks\b"),
    ("overview", r"\boverview\b|\b101\b"),
))
# Marketing and policy wording is only trusted in the title (a /large-business-services/ URL path is site structure).
TITLE_EXPLAINER_TERMS = _compile((
    ("strategy", r"\bstrategy\b"),
    ("vendor marketing", r"\bturnkey\b|\binnovative\b|\bsolutions\b|\bservices\b|\bdesign-?build\b"),
    ("policy", r"\bbill\b|\blegislation\b|\bsenate\b|\breform\b|\bplaybook\b"),
))
# Reference hosts count as explainer-like; social hosts are only down-weighted.
_REFERENCE_HOSTS = ("wikipedia.org", "ibisworld.com", "procurementiq.com", "quora.com")
_SOCIAL_HOSTS = ("facebook.com", "reddit.com", "youtube.com", "linkedin.com")
# Procurement portals and bid aggregators; a host match alone marks a hit as RFP-like (energy context still needed).
RFP_HOSTS = ("sam.gov", "bidnet.com", "bidnetdirect.com", "publicpurchase.com", "periscopeholdings.com",
             "bonfirehub.com", "planetbids.com", "demandstar.com", "opengov.com", "govtribe.com",
             "highergov.com", "merx.com", "ted.europa.eu", "biddingo.com", "findrfp.com", "rfpmart.com",
             "ionwave.net", "tenderlink.com", "tendersontime.com", "lightrfp.com", "govdash.com", "thebidlab.com")
# Utilities, public-power authorities and community-choice buyers that publish their own solicitations. Hosts in the
# discovery catalog's `domains` are added at runtime (LeadStore.set_official_hosts); .gov/.mil hosts (also .gov.xx and .xx.us) always count.
OFFICIAL_HOSTS = ("lipower.org", "psegliny.com", "dominionenergy.com", "nyseg.com", "hawaiianelectric.com",
                  "sdcommunitypower.org", "cleanpoweralliance.org", "svcleanenergy.org", "austinenergy.com",
                  "nationalfuel.com", "duke-energy.com", "ercot.com", "pjm.com", "aspower.com")


_STATE_US_HOST = re.compile(r"\.[a-z]{2}\.us$")  # city/county/state style hosts (ci.austin.tx.us), not any .us name


_GOV_HOST = re.compile(r"\.(?:gov|mil)$|\.(?:gov|mil)\.[a-z]{2}$")  # x.gov, x.gov.uk - not x.gov.evil.com


def _host_in(host: str, domains) -> str | None:
    return next((d for d in domains if host == d or host.endswith("." + d)), None)


# ----- deadline hint: a literal date in the snippet after deadline wording; never verified -----
_MONTHS = {"jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6, "jul": 7, "aug": 8, "sep": 9, "oct": 10,
           "nov": 11, "dec": 12}
_DATE_PATTERNS = (
    ("iso", re.compile(r"(?<![\d-])(20\d\d)-(\d\d)-(\d\d)(?!\d)")),
    ("long", re.compile(r"\b(jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|june?|july?|aug(?:ust)?|"
                        r"sept?(?:ember)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)\.?\s+(\d{1,2})(?:st|nd|rd|th)?,?"
                        r"\s+(20\d\d)\b", re.IGNORECASE)),
    ("us", re.compile(r"(?<![\d/])(\d{1,2})/(\d{1,2})/(20\d\d)(?![\d/])")),
)
# "due to the storm" and "submitted comments on <date>" are not deadlines; "submitted" needs "by/before".
_DEADLINE_WORD = re.compile(
    r"\b(?:due(?!\s+to\b)|deadline|submit(?:tals?)?|submitted(?=\s+(?:by|before|no later than)\b)|"
    r"submissions?(?=\s+(?:by|before|due|close|closes|no later than)\b)|closing|closes?)\b", re.IGNORECASE)
_DEADLINE_WINDOW = 80


def _parse_date(kind: str, groups: tuple[str, ...]) -> date | None:
    try:
        if kind == "iso":
            return date(int(groups[0]), int(groups[1]), int(groups[2]))
        if kind == "long":
            return date(int(groups[2]), _MONTHS[groups[0][:3].lower()], int(groups[1]))
        return date(int(groups[2]), int(groups[0]), int(groups[1]))
    except ValueError:
        return None


def deadline_hint(title: str, snippet: str) -> dict | None:
    """First date in the title/snippet that follows deadline wording (due, deadline, submit, closing, ...).

    Returns {"word": the deadline word, "text": the literal words, "date": ISO date} or None. It quotes what the snippet says; it does not
    check it, and a past date is not evidence that anything is open or closed.
    """
    text = " ".join(f"{title} {snippet}".split())
    found = sorted((m.start(), m.end(), kind, m.groups()) for kind, pattern in _DATE_PATTERNS
                   for m in pattern.finditer(text))
    previous_end = 0
    for start, end, kind, groups in found:
        # the deadline word must come after the previous date, so "Released <d1> ... Deadline: <d2>" picks d2
        words = list(_DEADLINE_WORD.finditer(text, max(previous_end, start - _DEADLINE_WINDOW), start))
        previous_end = end
        parsed = _parse_date(kind, groups)
        if parsed and words:
            return {"word": words[-1].group(0).lower(), "text": text[words[-1].start():end][:160],
                    "date": parsed.isoformat()}
    return None


def deadline_status(hint: dict | None, today: date) -> str | None:
    """Read-time only (never stored): how the snippet's date compares with `today`. 'future' does not mean open."""
    if not hint:
        return None
    try:
        when = date.fromisoformat(hint.get("date") or "")
    except ValueError:
        return "unknown"
    return "future" if when >= today else "past"


@dataclass(frozen=True)
class Classification:
    kind: str
    rfp: tuple[str, ...]
    project: tuple[str, ...]
    power: tuple[str, ...]
    context: tuple[str, ...] = ()
    explainer: tuple[str, ...] = ()
    deadline: dict | None = None
    score: int = 0
    reason: str = ""  # why a lead is OTHER (or an RFP hit by portal host alone); empty otherwise

    def matched(self) -> dict:
        return {"rfp": list(self.rfp), "project": list(self.project), "power": list(self.power),
                "context": list(self.context), "explainer": list(self.explainer),
                "deadline_hint": self.deadline, "reason": self.reason}


def classify(title: str, snippet: str, url: str, official_hosts=()) -> Classification:
    """Deterministic keyword heuristic and weighted score. It is not verification.

    RFP-like needs an RFP word (or a procurement-portal host) AND energy context, and a generic explainer is demoted
    unless it carries a strong signal. PROJECT-like needs a project word that names energy infrastructure (or a
    generic one plus energy context). Everything else is OTHER with a reason. The score only orders the lists.
    """
    parts = urlsplit(url)
    host = (parts.hostname or "").lower()
    path = re.sub(r"[-_/.+]+", " ", parts.path)
    text = f"{title}\n{snippet}\n{path}"
    listed = _host_in(host, OFFICIAL_HOSTS) or _host_in(host, tuple(official_hosts))
    official = bool(listed) or bool(_GOV_HOST.search(host)) or bool(_STATE_US_HOST.search(host))
    rfp_terms = _scan(RFP_TERMS, text)
    if "power procurement" not in rfp_terms and _TEMP_POWER.search(text) and _PROCUREMENT.search(text):
        rfp_terms = (*rfp_terms, "power procurement")  # e.g. a procurement-office letter about temporary generation
    if official:
        rfp_terms = (*rfp_terms, *_scan(_OFFICIAL_RFP_TERMS, f"{title}\n{snippet}\n{parts.path}"))
    portal = _host_in(host, RFP_HOSTS)
    rfp = (*rfp_terms, f"host:{portal}") if portal else rfp_terms
    project = _scan(PROJECT_TERMS, text)
    power = _scan(POWER_TERMS, text)
    context = tuple(dict.fromkeys(m.group(0).lower() for m in _ENERGY_CONTEXT.finditer(text)))
    has_context = bool(power or context or listed or _HOST_ENERGY.search(host))
    explainer = (*_scan(EXPLAINER_TERMS, f"{title}\n{path}"), *_scan(TITLE_EXPLAINER_TERMS, title))
    reference = _host_in(host, _REFERENCE_HOSTS)
    if reference:
        explainer = (*explainer, f"reference site: {reference}")
    hint = deadline_hint(title, snippet)

    strong_rfp = bool(portal or (official and rfp_terms) or hint or (_SPECIFIC_RFP.search(text) and power))
    strong_project = bool(_SIZE_TERMS & set(power))
    kind, reason = "OTHER", ""
    if rfp and not has_context and portal:
        kind, reason = "RFP", "procurement portal host, but no energy or power context in the snippet"
    elif rfp and not has_context:
        reason = "RFP wording but no energy or power context"
    elif rfp and explainer and not strong_rfp:
        reason = "explainer-like: " + ", ".join(explainer)
    elif rfp:
        kind = "RFP"
    if kind == "OTHER":
        specific = [t for t in project if t in _PROJECT_INHERENT or (t not in _PROJECT_WEAK and has_context)]
        if specific and explainer and not strong_project:
            reason = reason or "explainer-like: " + ", ".join(explainer)
        elif specific:
            kind, reason = "PROJECT", ""
        elif not reason:
            if project and set(project) <= _PROJECT_WEAK:
                reason = "permit wording only, no project"
            elif project:
                reason = "project wording but no energy or power context"
            else:
                reason = "no RFP or project words matched"

    score = sum(sorted((10 if p in _STRONG_POWER else 4 for p in power), reverse=True)[:4])  # strong 10, medium 4
    if _STRONG_POWER & set(_scan(POWER_TERMS, title)):
        score += 6 + 8 * bool(_scan(RFP_TERMS, title))  # the title itself says "<RFP> for temporary power"
    if kind == "RFP":
        score += 6 + 2 * bool(_SPECIFIC_RFP.search(text)) + 8 * bool(portal)
    elif kind == "PROJECT":
        score += 3 * min(sum(t in _PROJECT_INHERENT for t in project), 2)
        score += 4 * len({"announced", "planned"} & set(project))  # early-stage wording
        score += 2 * min(sum(t not in _PROJECT_INHERENT | _PROJECT_WEAK | {"announced", "planned"}
                             for t in project), 3)
        score += 4 * bool(_EVENT_VERB.search(title)) + 6 * bool(_NAMED_PROJECT.search(f"{title} {snippet}"))
    if kind == "RFP" and not has_context:
        score -= 12  # portal host alone: stays visible but ranks below every RFP with energy context
    score += (8 if kind == "RFP" else 2) * official + 8 * bool(hint)  # an official host matters most for solicitations
    score -= 10 * bool(explainer) + 4 * host.endswith(".edu") + 8 * bool(_host_in(host, _SOCIAL_HOSTS))
    return Classification(kind, rfp, project, power, context, explainer, hint, score, reason)
