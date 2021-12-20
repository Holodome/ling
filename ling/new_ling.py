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


@dataclasses.dataclass(frozen=True)
class Connection:
    predicate_idx: int = -1
    actant_idx: int = -1


class Sentence:
    """An interface for sentence analysis"""

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

        self.non_word_parts: list[str] = non_word_parts
        self.non_word_starts: list[int] = non_word_starts
        self.words: list[str] = words
        self.word_starts: list[int] = word_starts

        self.collocations: list[Collocation] = []
        self.connections: list[Connection] = []

    def is_word_marked(self, word_idx: int) -> bool:
        """Return if word of given index has semantic group assigned to it"""
        result = False
        for collocation in self.collocations:
            if word_idx in collocation.word_idxs:
                result = True
                break
        return result

    def find_word(self, word: str) -> int:
        """Check if word exists in sentence. Returns its index, -1 if not exist"""
        assert word.lower() == word
        result = -1
        for i, test_word in enumerate(self.words):
            if test_word == word:
                result = i
                break
        return result

    def get_pretty_string_with_words_for_collocation(self, collocation_idx: int) -> str:
        assert collocation_idx < len(self.collocations)
        result = ""
        collocation = self.collocations[collocation_idx]
        last_word_idx = -1
        for word_idx in collocation.word_idxs:
            word, word_start = self.words[word_idx], self.word_starts[word_idx]
            if last_word_idx != -1 and word_idx - last_word_idx != 1:
                result += " ... "
            elif word_idx - last_word_idx == 1:
                # This is ugly, but so is the data structure for sentence
                non_word_text_part_selection = {}
                if word_idx:
                    non_word_text_part_selection[self.non_word_starts[word_idx - 1]] = self.non_word_parts[word_idx - 1]
                non_word_text_part_selection[self.non_word_starts[word_idx]] = self.non_word_parts[word_idx],
                if word_idx < len(self.words) - 1:
                    non_word_text_part_selection[self.non_word_starts[word_idx + 1]] = self.non_word_parts[word_idx + 1]
                non_word_part = non_word_text_part_selection.get(word_start + len(word))
                if non_word_part is not None:
                    result += non_word_part
                else:
                    logging.warning("!!! Failed to find non word part")
            result += word
        return result

    def add_collocation_internal(self, col) -> int:
        """Adds collocation """
        result = len(self.collocations)
        self.collocations.append(col)
        return result

    def make_collocation(self, word_idxs: list[int], semantic_group: SemanticGroup) -> int:
        """Joins words from given index list in one collocation
           Words that are already in collocation are not touched
           If no words don't belong to any collocation already, do nothing
           Return index of collocation"""
        if sorted(word_idxs) != word_idxs:
            logging.warning("Words are not sorted")
        # Check that all indexes are correct
        assert all(map(lambda it: it < len(self.words), word_idxs))

        unassigned_words = list(filter(lambda word: not self.is_word_marked(word), word_idxs))

        result = -1
        if unassigned_words:
            col = Collocation(tuple(unassigned_words), semantic_group)
            result = self.add_collocation_internal(col)
        return result

    def make_collocation_text_part(self, start_idx: int, end_idx: int, semantic_group: SemanticGroup):
        """Makes collocation, marking all words not marked in current text region"""
        words_to_mark = []
        for idx, (word_str, word_start) in enumerate(zip(self.words, self.word_starts)):
            word_end = word_start + len(word_str)
            if start_idx <= word_end and end_idx >= word_start:
                words_to_mark.append(idx)

        return self.make_collocation(words_to_mark, semantic_group)

    def change_semantic_group_for_collocation(self, collocation_idx: int, new_semantic_group: SemanticGroup):
        assert collocation_idx < len(self.collocations)
        old_col = self.collocations[collocation_idx]
        new_col = Collocation(old_col.word_idxs, new_semantic_group)
        self.collocations[collocation_idx] = new_col

    def remove_collocations(self, col_ids: list[int]):
        """Removes collocations and all connections associated with them"""
        new_collocations = []
        mapped_indices = [-1 for _ in self.collocations]
        for idx, collocation in enumerate(self.collocations):
            if idx in col_ids:
                pass
            else:
                new_idx = len(new_collocations)
                new_collocations.append(collocation)
                mapped_indices[idx] = new_idx

        new_connections = []
        for connection in self.connections:
            if mapped_indices[connection.predicate_idx] != -1 and \
               mapped_indices[connection.actant_idx]:
                new_connections.append(connection)
        self.connections = new_connections

    def join_collocations(self, col_ids: list[int],
                          new_semantic_group: SemanticGroup):
        """Joins collocations. All associated connections involving old
        collocations use new one instead"""
        assert all(map(lambda it: it < len(self.collocations), col_ids))

        new_word_idxs = []
        for idx in col_ids:
            new_word_idxs.extend(self.collocations[idx].word_idxs)
        new_word_idxs = tuple(new_word_idxs)

        new_col = Collocation(new_word_idxs, new_semantic_group)
        new_col_idx = self.add_collocation_internal(new_col)

        new_connections = []
        for connection in self.connections:
            if connection.predicate_idx in col_ids and \
               connection.actant_idx in col_ids:
                pass
            elif connection.predicate_idx in col_ids:
                new_connections.append(Connection(new_col_idx, connection.actant_idx))
            elif connection.actant_idx in col_ids:
                new_connections.append(Connection(connection.predicate_idx,
                                                  new_col_idx))
            else:
                new_connections.append(connection)
        self.connections = new_connections
