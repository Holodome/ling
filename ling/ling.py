import enum
import dataclasses
import typing
from typing import List, Tuple, Union
import pymorphy2


morph = pymorphy2.MorphAnalyzer()


class PartOfSpeech(enum.Enum):
    NONE = 0x0
    NOUN = 0x1  # существительное
    ADJ = 0x2  # прилагательное
    COMP = 0x3  # компаратив
    VERB = 0x4  # глагол
    PRT = 0x5  # причастие
    GRND = 0x6  # деепричастие
    NUMR = 0x7  # числительное
    NPRO = 0x8  # местоимение
    PRED = 0x9  # предикатив
    PREP = 0xA  # предлог
    CONJ = 0xB  # союз
    PRCL = 0xC  # частица
    INTJ = 0xD  # междометие
    ADVB = 0xE  # наречие

    @staticmethod
    def from_pymorphy_str(pm: str):
        pymorphy_to_pos_dict = {
            "NOUN": PartOfSpeech.NOUN,
            "ADJF": PartOfSpeech.ADJ,
            "ADJS": PartOfSpeech.ADJ,
            "COMP": PartOfSpeech.COMP,
            "VERB": PartOfSpeech.VERB,
            "INFN": PartOfSpeech.VERB,
            "PRTF": PartOfSpeech.PRT,
            "PRTS": PartOfSpeech.PRT,
            "GRND": PartOfSpeech.GRND,
            "NUMR": PartOfSpeech.NUMR,
            "ADVB": PartOfSpeech.ADVB,
            "NPRO": PartOfSpeech.NPRO,
            "PRED": PartOfSpeech.PRED,
            "PREP": PartOfSpeech.PREP,
            "CONJ": PartOfSpeech.CONJ,
            "PRCL": PartOfSpeech.PRCL,
            "INTJ": PartOfSpeech.INTJ,
        }
        return pymorphy_to_pos_dict.get(pm)


SemanticGroup = typing.NewType("SemanticGroup", int)

COLOR_TABLE = [
    "red",
    "blue",
    "green",
    "yellow",
    "cyan",
    "orange"
]


def get_color_for_int(v):
    return COLOR_TABLE[v % len(COLOR_TABLE)]


def lines_intersect(a1, a2, b1, b2):
    return a2 >= b1 and b2 >= a1


@dataclasses.dataclass
class Collocation:
    word_idxs: List[int]
    semantic_group: SemanticGroup

    def remove_common_words(self, words: List[int]):
        self.word_idxs = list(filter(lambda it: it not in words, self.word_idxs))

    def does_exists(self):
        return len(self.word_idxs) != 0


@dataclasses.dataclass
class SentenceCtx:
    text: str = ""
    non_word_sentence_parts: List[str] = dataclasses.field(default_factory=list)
    non_word_sentence_part_starts: List[int] = dataclasses.field(default_factory=list)
    words: List[str] = dataclasses.field(default_factory=list)
    word_start_idxs: List[int] = dataclasses.field(default_factory=list)

    collocations: List[Collocation] = dataclasses.field(default_factory=list)
    collocation_id_freelist: [int] = dataclasses.field(default_factory=list)
    connections: List[Tuple[int, int]] = dataclasses.field(default_factory=list)

    def init_from_text(self, text: str):
        text = text.lower()
        non_word_sentence_parts = []
        non_word_sentence_part_starts = []
        words = []
        words_start_idxs = []
        cursor = 0
        while cursor < len(text):
            non_word_start = cursor
            while cursor < len(text) and not text[cursor].isalpha():
                cursor += 1
            non_word_sentence_parts.append(text[non_word_start:cursor])
            non_word_sentence_part_starts.append(non_word_start)
            word_start = cursor
            while cursor < len(text) and text[cursor].isalpha():
                cursor += 1
            words.append(text[word_start:cursor])
            words_start_idxs.append(word_start)

        self.__init__()
        self.text = text
        self.words = words
        self.word_start_idxs = words_start_idxs
        self.non_word_sentence_parts = non_word_sentence_parts
        self.non_word_sentence_part_starts = non_word_sentence_part_starts

    def add_collocation(self, word_idxs: List[int], semantic_group: SemanticGroup):
        assert semantic_group != 0
        # Add new entry
        idx = self.get_new_collocation_idx()
        coll = Collocation(word_idxs, semantic_group)
        self.collocations[idx] = coll
        return idx

    def get_new_collocation_idx(self) -> int:
        if self.collocation_id_freelist:
            result = self.collocation_id_freelist.pop()
        else:
            result = len(self.collocations)
            self.collocations.append(None)
        return result

    def mark_words(self, words: List[int], semantic_group: SemanticGroup) -> int:
        if words:
            return self.add_collocation(words, semantic_group)
        return -1

    def get_word_idxs_from_section(self, start_idx, end_idx) -> list:
        word_idxs = []
        for word_idx in range(len(self.word_start_idxs)):
            word_text = self.words[word_idx]
            word_start = self.word_start_idxs[word_idx]
            if lines_intersect(start_idx, end_idx, word_start, word_start + len(word_text)):
                word_idxs.append(word_idx)
        return word_idxs

    def mark_text_part(self, start_idx: int, end_idx: int, semantic_group: SemanticGroup):
        word_idxs = self.get_word_idxs_from_section(start_idx, end_idx)
        self.mark_words(word_idxs, semantic_group)

    def get_word_semantic_group(self, word_idx: int):
        semantic_group = 0
        for collocation in self.collocations:
            if word_idx in collocation.word_idxs:
                semantic_group = collocation.semantic_group
        return semantic_group

    def mark_text_part_soft(self, start_idx: int, end_idx: int, semantic_group: SemanticGroup):
        word_idxs = self.get_word_idxs_from_section(start_idx, end_idx)
        word_idxs = list(filter(lambda it: self.get_word_semantic_group(it) == 0, word_idxs))
        self.mark_words(word_idxs, semantic_group)

    def get_corresponding_collocation_id(self, word_idx: int) -> int:
        result = -1
        for i, collocation in enumerate(self.collocations):
            if word_idx in collocation.word_idxs:
                result = i
        return result

    def make_connection(self, col1_id, col2_id):
        connection = (col1_id, col2_id)
        # @TODO(hl): Using set for storing connections would be ideal in this situation,
        #   but don't want to make premature optimizations.
        #   Because later connections would have to maintain some lexical analysis
        if connection not in self.connections:
            self.connections.append(connection)

    def get_funny_html(self):
        html = ""
        for i, (non_word, word) in enumerate(zip(self.non_word_sentence_parts, self.words)):
            word_semantic_group = self.get_word_semantic_group(i)
            if word_semantic_group != 0:
                color = get_color_for_int(word_semantic_group)
                word = f"<font color={color}>{word}</font>"

            html += non_word
            html += word
        return html

    def get_funny_html_detailed(self):
        # @TODO(hl): Not implemented
        html = ""
        return html

    def remove_collocations(self, collocation_idxs: List[int]):
        new_collocations = []
        for collocation_idx, collocation in enumerate(self.collocations):
            if collocation_idx not in collocation_idxs:
                new_collocations.append(collocation)
        self.collocations = new_collocations
        # Remove connections with deleted collocations
        new_connections = []
        for connection in self.connections:
            if connection[0] in collocation_idxs or connection[1] in collocation_idxs:
                ...
            else:
                new_connections.append(connection)
        self.connections = new_connections

    def join_collocations(self, collocation_idxs: List[int]):
        print(collocation_idxs)
        if len(collocation_idxs) > 1:
            collocations_to_join = list(map(lambda it: self.collocations[it], collocation_idxs))
            # @HACK(hl): Probably want to warn when semantic_groups are different
            new_semantic_group = collocations_to_join[0].semantic_group
            new_words = []
            for col in collocations_to_join:
                new_words.extend(col.word_idxs)
            new_idx = self.add_collocation(new_words, new_semantic_group)
            print(new_idx)
            # add connections
            new_connections = []
            for connection in self.connections:
                if not (connection[0] in collocation_idxs and connection[1] in collocation_idxs):
                    if connection[0] in collocation_idxs:
                        new_conn = (new_idx, connection[1])
                    elif connection[1] in collocation_idxs:
                        new_conn = (connection[0], new_idx)
                    else:
                        new_conn = connection
                    new_connections.append(new_conn)
            self.connections = new_connections
            self.remove_collocations(collocation_idxs)

    def change_semantic_group(self, collocation_idx: int, semantic_group: SemanticGroup):
        self.collocations[collocation_idx].semantic_group = semantic_group

    def delete_connections(self, connections: List[int]):
        new_connections = []
        for i, connection in enumerate(self.connections):
            if i not in connections:
                new_connections.append(connection)
        self.connections = new_connections


@dataclasses.dataclass
class TextCtx:
    text = ""
    sentences: List[str] = dataclasses.field(default_factory=list)  # text inside is stripped
    sentence_start_idxs: List[int] = dataclasses.field(default_factory=list)
    sentence_ctxs: List[SentenceCtx] = dataclasses.field(default_factory=list)

    def init_for_text(self, text):
        sentences = []
        sentence_start_idxs = []
        sentence_start = 0
        for cursor, symb in enumerate(text):
            if symb == ".":
                sentences.append(text[sentence_start:cursor])
                sentence_start_idxs.append(sentence_start)
                sentence_start = cursor + 1
        sentence_ctxs = [SentenceCtx() for _ in sentences]
        for sentence, ctx in zip(sentences, sentence_ctxs):
            sentence = sentence.strip()
            ctx.init_from_text(sentence)

        self.__init__()
        self.text = text
        self.sentences = sentences
        self.sentence_start_idxs = sentence_start_idxs
        self.sentence_ctxs = sentence_ctxs

    def get_sentence_idx_from_cursor(self, cursor: int) -> int:
        if not self.sentences:
            return -1

        if cursor >= self.sentence_start_idxs[-1]:
            edit_idx = len(self.sentence_start_idxs) - 1
        else:
            edit_idx = -1
            for sentence_idx in range(len(self.sentences) - 1):
                start = self.sentence_start_idxs[sentence_idx]
                next_start = self.sentence_start_idxs[sentence_idx + 1]
                if start <= cursor < next_start:
                    edit_idx = sentence_idx
                    break
            assert edit_idx != -1
        return edit_idx

    def start_sentence_edit(self, index: int):
        edit_idx = self.get_sentence_idx_from_cursor(index)
        if edit_idx != -1:
            sentence_ctx = self.sentence_ctxs[edit_idx]
            return sentence_ctx
        return None


@dataclasses.dataclass
class Word:
    word: str
    initial_form: Union[str, None]
    part_of_speech: PartOfSpeech

    @staticmethod
    def create(word: str):
        parse_results = morph.parse(word)
        if parse_results:
            form = parse_results[0]
            initial_form = form.normal_form
            # NOTE(hl): Because we don't do deep morphological analysis it is enough for us that text is equals
            # because the only other parameter we currently have is
            initial_form = initial_form if initial_form != word else None
            part_of_speech = PartOfSpeech.from_pymorphy_str(form.tag.POS)
            word = Word(word, initial_form, part_of_speech)

            return word
        assert False

