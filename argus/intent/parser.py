"""
Deterministic, rule-based text classifier for the ArgusOS Intent Router.

Purpose:
    Classify a piece of natural-language text into one of the five
    IntentType values, with a deterministic confidence score and any
    trivially-recognizable entities, per
    factory/packages/009_INTENT_ROUTER.md. This module is pure and has
    no dependencies on the Event Bus, IService, or anything else in
    this package - it is a plain function of its input, which is what
    makes it fully unit-testable in isolation and genuinely
    deterministic.

Responsibilities:
    - Apply a small, fixed set of keyword/prefix rules, in a fixed
      precedence order, to classify text.
    - Return a ParsedText result: (name, confidence, entities,
      parameters). IntentRouter.parse() wraps this in a full Intent
      (adding id and timestamp).

Non-Responsibilities:
    - No AI, no machine learning, no external libraries, and no
      regex - every rule here is a plain string `startswith`/`in`
      check against a short, explicit keyword list, per this
      package's explicit "simple rule-based parsing only" scope.
    - No attempt at general-purpose natural language understanding:
      the keyword lists are small and directly grounded in this
      package's given examples, not an attempt to exhaustively cover
      English.
    - Does not construct an Intent (no id/timestamp generation) and
      does not publish anything; both are IntentRouter's
      responsibility.

Dependencies:
    argus.intent.intent (IntentType), for the classification result.

Rule Precedence (first match wins; deterministic and fixed):
    1. QUESTION  - text ends with "?", or starts with a question word.
    2. COMMAND   - text starts with a known imperative verb.
    3. MEMORY    - text starts with (strong) or contains (weaker) a
                   memory keyword.
    4. SCHEDULE  - text starts with (strong) or contains (weaker) a
                   schedule keyword.
    5. UNKNOWN   - fallback; confidence 0.0.

Confidence Scheme (deterministic, fixed constants - no fuzzy scoring):
    1.0 - a "strong" match (ends with "?"; starts with the keyword).
    0.6 - a "weak" match (the keyword appears elsewhere in the text).
    0.0 - no match (UNKNOWN).
"""

from dataclasses import dataclass, field
from typing import Any, Dict, Mapping

from argus.intent.intent import IntentType

STRONG_CONFIDENCE = 1.0
WEAK_CONFIDENCE = 0.6
NO_MATCH_CONFIDENCE = 0.0

# Small, fixed keyword lists, each directly grounded in
# factory/packages/009_INTENT_ROUTER.md's given examples. Not intended
# to be an exhaustive vocabulary - see this module's
# Non-Responsibilities.
QUESTION_WORDS = ("what", "who", "when", "where", "why", "how", "is", "are", "can", "could", "would", "does", "do", "did")
COMMAND_VERBS = ("shutdown", "start", "stop", "restart", "open", "close", "run", "execute", "cancel", "delete", "create")
MEMORY_KEYWORDS = ("remember", "recall", "note")
SCHEDULE_KEYWORDS = ("remind", "schedule")


@dataclass(frozen=True)
class ParsedText:
    """
    The pure result of classifying one piece of text.

    Purpose:
        Carry parse_text()'s result to IntentRouter.parse(), which
        wraps it in a full Intent.
    """

    name: IntentType
    confidence: float
    entities: Mapping[str, Any] = field(default_factory=dict)
    parameters: Mapping[str, Any] = field(default_factory=dict)


def parse_text(text: str) -> ParsedText:
    """
    Classify `text` into an IntentType, deterministically.

    Parameters:
        text: The raw text to classify. Assumed already validated as
            a string by the caller (IntentRouter.parse());
            parse_text() itself does not raise for any string input,
            including an empty or whitespace-only one, which resolves
            to UNKNOWN.

    Returns:
        A ParsedText with a deterministic (name, confidence, entities,
        parameters) for the given text.
    """
    parameters: Dict[str, Any] = {"raw_text": text}
    normalized = text.strip().lower()

    if not normalized:
        return ParsedText(IntentType.UNKNOWN, NO_MATCH_CONFIDENCE, {}, parameters)

    if normalized.endswith("?"):
        return ParsedText(IntentType.QUESTION, STRONG_CONFIDENCE, {}, parameters)

    for word in QUESTION_WORDS:
        if _starts_with_word(normalized, word):
            return ParsedText(IntentType.QUESTION, STRONG_CONFIDENCE, {}, parameters)

    for verb in COMMAND_VERBS:
        if _starts_with_word(normalized, verb):
            return ParsedText(IntentType.COMMAND, STRONG_CONFIDENCE, {"verb": verb}, parameters)

    memory_match = _match_keywords(normalized, MEMORY_KEYWORDS)
    if memory_match is not None:
        keyword, confidence = memory_match
        entities: Dict[str, Any] = {"keyword": keyword}
        if _starts_with_word(normalized, keyword):
            subject = text[len(keyword):].strip(" \t\n:,-")
            if subject:
                entities["subject"] = subject
        return ParsedText(IntentType.MEMORY, confidence, entities, parameters)

    schedule_match = _match_keywords(normalized, SCHEDULE_KEYWORDS)
    if schedule_match is not None:
        keyword, confidence = schedule_match
        return ParsedText(IntentType.SCHEDULE, confidence, {"keyword": keyword}, parameters)

    return ParsedText(IntentType.UNKNOWN, NO_MATCH_CONFIDENCE, {}, parameters)


def _starts_with_word(normalized: str, word: str) -> bool:
    """True if `normalized` is exactly `word`, or starts with `word`
    followed by whitespace (so "remember" matches "remember" and
    "remember this" but not "remembering")."""
    return normalized == word or normalized.startswith(word + " ")


def _match_keywords(normalized: str, keywords):
    """Return (keyword, confidence) for the first keyword that matches
    `normalized` - STRONG_CONFIDENCE if `normalized` starts with it,
    WEAK_CONFIDENCE if it merely appears elsewhere - or None if no
    keyword in `keywords` appears at all."""
    for keyword in keywords:
        if _starts_with_word(normalized, keyword):
            return keyword, STRONG_CONFIDENCE
    for keyword in keywords:
        if keyword in normalized:
            return keyword, WEAK_CONFIDENCE
    return None
