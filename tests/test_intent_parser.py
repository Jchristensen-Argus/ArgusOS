"""Unit tests for argus.intent.parser (parse_text, ParsedText)."""

import unittest

from argus.intent import IntentType
from argus.intent.parser import (
    NO_MATCH_CONFIDENCE,
    STRONG_CONFIDENCE,
    WEAK_CONFIDENCE,
    ParsedText,
    parse_text,
)


class GivenExamplesTests(unittest.TestCase):
    """The four classification examples given explicitly in
    factory/packages/009_INTENT_ROUTER.md."""

    def test_remember_my_dentist_appointment_is_memory(self):
        result = parse_text("Remember my dentist appointment")

        self.assertEqual(result.name, IntentType.MEMORY)
        self.assertEqual(result.confidence, STRONG_CONFIDENCE)
        self.assertEqual(result.entities["keyword"], "remember")
        self.assertEqual(result.entities["subject"], "my dentist appointment")

    def test_remind_me_tomorrow_is_schedule(self):
        result = parse_text("Remind me tomorrow")

        self.assertEqual(result.name, IntentType.SCHEDULE)
        self.assertEqual(result.confidence, STRONG_CONFIDENCE)
        self.assertEqual(result.entities["keyword"], "remind")

    def test_what_is_corrugated_board_is_question(self):
        result = parse_text("What is corrugated board?")

        self.assertEqual(result.name, IntentType.QUESTION)
        self.assertEqual(result.confidence, STRONG_CONFIDENCE)

    def test_shutdown_argus_is_command(self):
        result = parse_text("Shutdown Argus")

        self.assertEqual(result.name, IntentType.COMMAND)
        self.assertEqual(result.confidence, STRONG_CONFIDENCE)
        self.assertEqual(result.entities["verb"], "shutdown")


class QuestionClassificationTests(unittest.TestCase):
    def test_question_mark_alone_is_sufficient(self):
        result = parse_text("corrugated board?")

        self.assertEqual(result.name, IntentType.QUESTION)
        self.assertEqual(result.confidence, STRONG_CONFIDENCE)

    def test_leading_question_word_without_question_mark(self):
        for word in ("what", "who", "when", "where", "why", "how", "is", "are", "can", "could", "would", "does", "do", "did"):
            with self.subTest(word=word):
                result = parse_text(f"{word} something happened")
                self.assertEqual(result.name, IntentType.QUESTION)
                self.assertEqual(result.confidence, STRONG_CONFIDENCE)

    def test_question_word_as_substring_not_prefix_does_not_match(self):
        # "cando" is not the word "can" followed by a space/end.
        result = parse_text("candor is a virtue")

        self.assertNotEqual(result.name, IntentType.QUESTION)

    def test_question_classification_is_case_insensitive(self):
        result = parse_text("WHAT time is it")

        self.assertEqual(result.name, IntentType.QUESTION)


class CommandClassificationTests(unittest.TestCase):
    def test_leading_command_verb(self):
        for verb in ("shutdown", "start", "stop", "restart", "open", "close", "run", "execute", "cancel", "delete", "create"):
            with self.subTest(verb=verb):
                result = parse_text(f"{verb} the thing")
                self.assertEqual(result.name, IntentType.COMMAND)
                self.assertEqual(result.confidence, STRONG_CONFIDENCE)
                self.assertEqual(result.entities["verb"], verb)

    def test_command_verb_must_be_the_leading_word(self):
        result = parse_text("please stop the task")

        self.assertNotEqual(result.name, IntentType.COMMAND)

    def test_command_classification_is_case_insensitive(self):
        result = parse_text("STOP everything")

        self.assertEqual(result.name, IntentType.COMMAND)
        self.assertEqual(result.entities["verb"], "stop")


class MemoryClassificationTests(unittest.TestCase):
    def test_leading_memory_keyword_extracts_subject(self):
        result = parse_text("recall the meeting notes")

        self.assertEqual(result.name, IntentType.MEMORY)
        self.assertEqual(result.confidence, STRONG_CONFIDENCE)
        self.assertEqual(result.entities["keyword"], "recall")
        self.assertEqual(result.entities["subject"], "the meeting notes")

    def test_memory_keyword_mid_sentence_is_weak_confidence(self):
        result = parse_text("please note that the sky is blue")

        self.assertEqual(result.name, IntentType.MEMORY)
        self.assertEqual(result.confidence, WEAK_CONFIDENCE)

    def test_leading_memory_keyword_with_no_remaining_subject_omits_subject_key(self):
        result = parse_text("remember")

        self.assertEqual(result.name, IntentType.MEMORY)
        self.assertNotIn("subject", result.entities)

    def test_leading_memory_keyword_extracts_subject_after_trailing_space(self):
        result = parse_text("note buy milk")

        self.assertEqual(result.entities["subject"], "buy milk")

    def test_keyword_immediately_followed_by_punctuation_is_not_a_leading_match(self):
        # "note:" does not satisfy the word-boundary check (keyword
        # followed by a space or end-of-string), so this falls through
        # to the substring/weak-confidence path with no subject
        # extracted - a known, documented limitation of the simple
        # rule-based matcher (no punctuation normalization).
        result = parse_text("note: buy milk")

        self.assertEqual(result.name, IntentType.MEMORY)
        self.assertEqual(result.confidence, WEAK_CONFIDENCE)
        self.assertNotIn("subject", result.entities)


class ScheduleClassificationTests(unittest.TestCase):
    def test_leading_schedule_keyword(self):
        for keyword in ("remind", "schedule"):
            with self.subTest(keyword=keyword):
                result = parse_text(f"{keyword} me at noon")
                self.assertEqual(result.name, IntentType.SCHEDULE)
                self.assertEqual(result.confidence, STRONG_CONFIDENCE)
                self.assertEqual(result.entities["keyword"], keyword)

    def test_schedule_keyword_mid_sentence_is_weak_confidence(self):
        result = parse_text("can you schedule a meeting for me")

        # "can" is a leading question word, so this actually classifies
        # as QUESTION under the documented precedence order (question
        # is checked before command/memory/schedule). Use a sentence
        # with no leading question/command word instead.
        result = parse_text("please schedule a meeting for me")
        self.assertEqual(result.name, IntentType.SCHEDULE)
        self.assertEqual(result.confidence, WEAK_CONFIDENCE)


class PrecedenceTests(unittest.TestCase):
    """Fixed precedence order: question mark/word, then command verb,
    then memory keyword, then schedule keyword, then unknown."""

    def test_question_mark_takes_precedence_over_trailing_keywords(self):
        result = parse_text("remember to buy milk?")

        self.assertEqual(result.name, IntentType.QUESTION)

    def test_leading_question_word_takes_precedence_over_command_verb(self):
        result = parse_text("does start work")

        self.assertEqual(result.name, IntentType.QUESTION)

    def test_leading_command_verb_takes_precedence_over_memory_keyword(self):
        result = parse_text("delete my remembered notes")

        self.assertEqual(result.name, IntentType.COMMAND)


class UnknownAndEdgeCaseTests(unittest.TestCase):
    def test_empty_string_is_unknown(self):
        result = parse_text("")

        self.assertEqual(result.name, IntentType.UNKNOWN)
        self.assertEqual(result.confidence, NO_MATCH_CONFIDENCE)

    def test_whitespace_only_is_unknown(self):
        result = parse_text("   \t\n  ")

        self.assertEqual(result.name, IntentType.UNKNOWN)
        self.assertEqual(result.confidence, NO_MATCH_CONFIDENCE)

    def test_gibberish_is_unknown(self):
        result = parse_text("xyzzy plugh qwerty")

        self.assertEqual(result.name, IntentType.UNKNOWN)
        self.assertEqual(result.confidence, NO_MATCH_CONFIDENCE)

    def test_raw_text_parameter_is_always_the_original_text(self):
        text = "  Remember Milk  "
        result = parse_text(text)

        self.assertEqual(result.parameters["raw_text"], text)

    def test_unknown_result_has_no_entities(self):
        result = parse_text("gibberish")

        self.assertEqual(result.entities, {})

    def test_result_is_a_parsed_text_instance(self):
        result = parse_text("hello")

        self.assertIsInstance(result, ParsedText)

    def test_parse_text_never_raises_for_any_string_content(self):
        samples = ["", " ", "?", "a", "12345", "!!!", "\ttab\n", "😀 emoji"]

        for sample in samples:
            with self.subTest(sample=repr(sample)):
                result = parse_text(sample)
                self.assertIsInstance(result, ParsedText)


if __name__ == "__main__":
    unittest.main()
