import dataclasses
import logging
import typing

from ling.session import Session

SemanticGroup = typing.NewType("SemanticGroup", int)

# https://en.wikipedia.org/wiki/Web_colors#HTML_color_names
COLOR_TABLE = [
    "silver",
    "gray",
    "red",
    "maroon",
    "yellow",
    "olive",
    "lime",
    "green",
    "aqua",
    "teal",
    "blue",
    "navy",
    "fuchsia",
    "purple",
]


def get_color_for_int(v: int):
    return COLOR_TABLE[v % len(COLOR_TABLE)]


@dataclasses.dataclass(frozen=True)
class Collocation:
    """Collocation that belongs to one sentence"""
    word_idxs: tuple[int]
    sg: SemanticGroup


@dataclasses.dataclass(frozen=True)
class Connection:
    predicate_idx: int = -1
    actant_idx: int = -1


class Sentence:
    """An interface for sentence analysis"""

    def __init__(self, session: Session, text: str):
        self.session = session
        """Creates sentence context for collocation and con creation"""
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

        self.cols: list[Collocation] = []
        self.cons: list[Connection] = []

    def get_word_sg(self, word_idx: int) -> int:
        """Return if word of given index has semantic group assigned to it.
           If it has, return semantic group number. Otherwise return 0"""
        result = 0
        for col in self.cols:
            if word_idx in col.word_idxs:
                result = col.sg
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

    def get_pretty_string_with_words_for_col(self, col_idx: int) -> str:
        result = ""
        col = self.cols[col_idx]
        last_word_idx = -1
        print(col)
        for word_idx in col.word_idxs:
            word, word_start = self.words[word_idx], self.word_starts[word_idx]
            if last_word_idx != -1 and word_idx - last_word_idx != 1:
                # If words are not adjacent insert ellipsis
                result += " ... "
            elif word_idx - last_word_idx == 1:
                non_word_part = ""
                # Find the non word part connecting two adjacent words
                cur = self.word_starts[last_word_idx] + len(self.words[last_word_idx])
                print(cur, self.non_word_starts)
                for start, part in zip(self.non_word_starts, self.non_word_parts):
                    if start == cur:
                        non_word_part = part
                        break
                result += non_word_part
            result += word
            last_word_idx = word_idx
        return result

    def add_col_internal(self, col) -> int:
        """Adds collocation and returns its index"""
        result = len(self.cols)
        self.cols.append(col)
        return result

    def make_col(self, word_idxs: list[int], semantic_group: SemanticGroup) -> int:
        """Joins words from given index list in one collocation
           Words that are already in collocation are not touched
           If no words don't belong to any collocation already, do nothing
           Return index of collocation"""

        # Check that all indexes are correct
        assert all(map(lambda it: it < len(self.words), word_idxs))

        unassigned_words = list(filter(lambda word: not self.get_word_sg(word), word_idxs))

        result = -1
        if unassigned_words:
            col = Collocation(tuple(unassigned_words), semantic_group)
            result = self.add_col_internal(col)
        return result

    def make_col_text_part(self, start_idx: int, end_idx: int, semantic_group: SemanticGroup):
        """Makes collocation, marking all words not marked in current text region"""
        words_to_mark = []
        for idx, (word_str, word_start) in enumerate(zip(self.words, self.word_starts)):
            word_end = word_start + len(word_str)
            if start_idx <= word_end and end_idx >= word_start:
                words_to_mark.append(idx)

        return self.make_col(words_to_mark, semantic_group)

    def change_semantic_group_for_col(self, col_idx: int, new_semantic_group: SemanticGroup):
        """Changes semantic group for collocation"""
        assert col_idx < len(self.cols)
        old_col = self.cols[col_idx]
        new_col = Collocation(old_col.word_idxs, new_semantic_group)
        self.cols[col_idx] = new_col

    def remove_cols(self, col_ids: list[int]):
        """Removes cols and all cons associated with them"""
        new_cols = []
        mapped_indices = [-1 for _ in self.cols]
        for idx, col in enumerate(self.cols):
            if idx in col_ids:
                pass
            else:
                new_idx = len(new_cols)
                new_cols.append(col)
                mapped_indices[idx] = new_idx

        new_cons = []
        for con in self.cons:
            if mapped_indices[con.predicate_idx] != -1 and \
                    mapped_indices[con.actant_idx]:
                new_cons.append(con)
        self.cons = new_cons

    def join_cols(self, col_ids: list[int],
                  new_sg: SemanticGroup):
        """Joins collocations. All associated cons involving old
        collocations use new one instead

        Change cons containing each of connected collocations to cons with joined collocation
        If somehow invalid connection appears, ingore it"""
        assert all(map(lambda it: it < len(self.cols), col_ids))

        new_word_idxs = []
        for idx in col_ids:
            new_word_idxs.extend(self.cols[idx].word_idxs)
        new_word_idxs = tuple(new_word_idxs)

        new_col = Collocation(new_word_idxs, new_sg)
        new_col_idx = self.add_col_internal(new_col)

        pred_sg = self.session.get_pred_sg()
        new_cons = []
        for con in self.cons:
            new_con = con
            if con.predicate_idx in col_ids and \
                    con.actant_idx in col_ids:
                pass
            elif con.predicate_idx in col_ids:
                new_con = Connection(new_col_idx, con.actant_idx)
            elif con.actant_idx in col_ids:
                new_con = Connection(con.predicate_idx, new_col_idx)

            if self.cols[new_con.predicate_idx].sg != pred_sg or \
                    self.cols[new_con.predicate_idx].sg == pred_sg:
                continue

            new_cons.append(new_con)
        self.cons = new_cons

    def make_con(self, pred_idx: int, actant_idx: int):
        """Makes con with collocations which indices given in list
           If collocation already is connected, overwrite old con"""
        col_idxs = (pred_idx, actant_idx)
        pred_sg = self.session.get_pred_sg()
        assert self.cols[pred_idx].sg == pred_sg and \
               self.cols[actant_idx].sg != pred_sg

        new_cons = []
        for con in self.cons:
            if con.predicate_idx in col_idxs or \
                    con.actant_idx in col_idxs:
                pass
            else:
                new_cons.append(con)

        con = Connection(pred_idx, actant_idx)
        new_cons.append(con)

    def make_con_from_list(self, idxs: list[int]):
        """Makes connection based on collocation indices from list.
           Predicate must be in the list. If several predicates found, ones other than first are not connected"""
        raise NotImplementedError

    def is_default_cons_makeable(self):
        """Consider default cons makeable if predicate count is one"""
        pred_sg = self.session.get_pred_sg()
        pred_count = sum(map(lambda it: it.sg == pred_sg, self.cols))
        return pred_count == 1

    def make_default_cons(self):
        """Makes default cons by joining collocations with first found predicate"""
        pred_sg = self.session.get_pred_sg()
        if not self.is_default_cons_makeable():
            logging.info("Attempt to make_default_cons with >1 predicates")
            return
        pred_idx = -1
        for idx, col in enumerate(self.cols):
            if col.sg == pred_sg:
                pred_idx = idx
                break
        assert pred_idx != -1

        # We can safely clear the connection list because all semantic groups would be used and nothing should remain
        for idx, col in enumerate(self.cols):
            if idx != pred_idx:
                self.make_con(pred_idx, idx)
        assert len(self.cons) == len(self.cols) - 1

    def get_colored_html(self) -> str:
        """Returns html version of the sentence with collocations colored"""

        def get_word_of_idx_colored(idx):
            word = self.words[idx]
            kind = self.get_word_sg(idx)
            if kind:
                color = get_color_for_int(kind)
                word = f"<font color={color}>{word}</font>"
            return word

        html = ""
        word_idx = 0
        non_word_idx = 0
        while word_idx < len(self.words) or \
                non_word_idx < len(self.non_word_parts):
            if word_idx == len(self.words):
                while non_word_idx < len(self.non_word_parts):
                    html += self.non_word_parts[non_word_idx]
                    non_word_idx += 1
            elif non_word_idx == len(self.non_word_parts):
                while word_idx < len(self.words):
                    html += get_word_of_idx_colored(word_idx)
                    word_idx += 1
            else:
                if self.word_starts[word_idx] < self.non_word_starts[non_word_idx]:
                    html += get_word_of_idx_colored(word_idx)
                    word_idx += 1
                else:
                    html += self.non_word_parts[non_word_idx]
                    non_word_idx += 1
        return html

    def remove_cons(self, idxs: list[int]):
        """Deletes connections of given indices"""
        raise NotImplementedError

    def remove_words_from_col(self, col_idx: int, word_idxs: list[int]):
        """Removes given word indexes from collocation.
           Indices are for collocation word list, not for the sentence words
           If number of words deleted equals total number of words in collocation,
           delete collocation instead"""
        raise NotImplementedError
