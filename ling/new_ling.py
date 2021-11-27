import enum
import dataclasses
import logging
import typing

import pymorphy2


morph = pymorphy2.MorphAnalyzer()
SemanticGroup = typing.NewType("SemanticGroup", int)

# TODO(hl): Add more
COLOR_TABLE = [
    "red",
    "blue",
    "green",
    "yellow",
    "cyan",
    "orange"
]


def get_color_for_int(v: int):
    return COLOR_TABLE[v % len(COLOR_TABLE)]


@dataclasses.dataclass(frozen=True)
class Collocation:
    """Collocation that belongs to one sentence"""
    word_idxs: tuple[int]
    semantic_group: SemanticGroup


class Sentence:
    """An interface for sentence analysis

    Features:
    1) Add collocation
    2)"""

    def __init__(self, text: str):
        """Creates sentence context for collocation and connection creation"""
        self.text: str = text
        # Construct the information about sentence text
        # Starts arrays contain index in text
        non_word_parts = []
        non_word_starts = []
        words = []
        word_starts = []
        # Iterate
        text = text.lower()
        cursor = 0
        while cursor < len(text):
            if text[cursor].isalnum():
                word_start = cursor
                while cursor < len(text) and text[cursor].isalnum():
                    cursor += 1
                words.append(text[word_start:cursor])
                word_starts.append(word_start)
            else:
                non_word_start = cursor
                while cursor < len(text) and not text[cursor].isalnum():
                    cursor += 1
                non_word_parts.append(text[non_word_start:cursor])
                non_word_starts.append(non_word_start)

        self.non_word_parts = non_word_parts
        self.non_word_starts = non_word_starts
        self.words = words
        self.word_starts = word_starts

        self.collocations: list[Collocation] = []
        self.connections = []

    def make_collocation(self, word_idxs: list[int], semantic_group: SemanticGroup):
        """Joins words from given index list in one collocation
           Words that are already in collocation are not touched
           If no words don't belong to any collocation already, do nothing"""
        if sorted(word_idxs) != word_idxs:
            logging.warning("Words are not sorted")
        # Check that all indexes are correct
        assert all(map(lambda it: it < len(self.words), word_idxs))

        unassigned_words = word_idxs
        for collocation in self.collocations:
            unassigned_words = list(filter(lambda word: word not in collocation.word_idxs, unassigned_words))

        if unassigned_words:
            col = Collocation(tuple(unassigned_words), semantic_group)
            self.collocations.append(col)
