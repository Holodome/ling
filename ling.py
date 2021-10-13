import enum
import dataclasses
from typing import List, DefaultDict, Tuple, Set, Dict, NewType
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


class LingKind(enum.Enum):
    ADJUNCT = 0x0
    AGENT = 0x1
    PREDICATE = 0x2
    OBJECT = 0x3
    INSTRUMENT = 0x4
    # Новые типы идут ниже

    NONE = ADJUNCT


LING_KIND_STRINGS = [
    "Адъюнкт",
    "Агент",
    "Предикат",
    "Объект",
    "Инструмент",
]

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


def text_words_space_separated(text):
    text_filtered = "".join(map(lambda it: it if it.isalpha() else " ", text))
    text_filtered = " ".join(text_filtered.split())
    return text_filtered


def lines_intersect(a1, a2, b1, b2):
    return a2 >= b1 and b2 >= a1


@dataclasses.dataclass
class Collocation:
    words: List[int]
    kind: LingKind

    def remove_common_words(self, words: List[int]):
        self.words = list(filter(lambda it: it not in words, self.words))

    def does_exists(self):
        return len(self.words) != 0


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

    def init_from_text(self, text):
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

    def add_collocation(self, word_idxs: List[int], kind: LingKind):
        for collocation in self.collocations:
            collocation.remove_common_words(word_idxs)
        self.collocations = list(filter(lambda it: it.does_exists(), self.collocations))

        idx = self.get_new_collocation_idx()
        coll = Collocation(word_idxs, kind)
        self.collocations[idx] = coll
        return idx

    def get_new_collocation_idx(self) -> int:
        if self.collocation_id_freelist:
            result = self.collocation_id_freelist.pop()
        else:
            result = len(self.collocations)
            self.collocations.append(None)
        return result

    def mark_words(self, words: List[int], kind: LingKind) -> int:
        if words:
            return self.add_collocation(words, kind)
        return -1

    def get_word_idxs_from_section(self, start_idx, end_idx) -> list:
        word_idxs = []
        for word_idx in range(len(self.word_start_idxs)):
            word_text = self.words[word_idx]
            word_start = self.word_start_idxs[word_idx]
            if lines_intersect(start_idx, end_idx, word_start, word_start + len(word_text)):
                word_idxs.append(word_idx)
        return word_idxs

    def mark_text_part(self, start_idx: int, end_idx: int, kind: LingKind):
        word_idxs = self.get_word_idxs_from_section(start_idx, end_idx)
        self.mark_words(word_idxs, kind)

    def get_word_kind(self, word_idx: int):
        kind = LingKind.ADJUNCT
        for collocation in self.collocations:
            if word_idx in collocation.words:
                kind = collocation.kind
        return kind

    def mark_text_part_soft(self, start_idx: int, end_idx: int, kind: LingKind):
        word_idxs = self.get_word_idxs_from_section(start_idx, end_idx)
        word_idxs = list(filter(lambda it: self.get_word_kind(it) == LingKind.ADJUNCT, word_idxs))
        self.mark_words(word_idxs, kind)

    def get_corresponding_collocation_id(self, word_idx: int) -> int:
        result = -1
        for i, collocation in enumerate(self.collocations):
            if word_idx in collocation.words:
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
            word_kind = self.get_word_kind(i)
            if word_kind != LingKind.ADJUNCT:
                color = get_color_for_int(word_kind.value)
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

    def join_collocations(self, collocation_idxs: List[int]):
        if len(collocation_idxs) > 1:
            collocations_to_join = list(map(lambda it: self.collocations[it], collocation_idxs))
            # @HACK(hl): Probably want to warn when kinds are different
            new_kind = collocations_to_join[0].kind
            new_words = []
            for col in collocations_to_join:
                new_words.extend(col.words)
            self.add_collocation(new_words, new_kind)

    def change_kind(self, collocation_idx: int, kind: LingKind):
        self.collocations[collocation_idx].kind = kind

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


WordID = NewType("WordID", int)


@dataclasses.dataclass
class GlobalLingContext:
    words: Dict[WordID, str] = dataclasses.field(default_factory=dict)
    collocations: List[Tuple[List[WordID], LingKind]] = dataclasses.field(default_factory=list)

    def add_word(self, word: str) -> WordID:
        str_hash = hash(word)
        word_id = WordID(str_hash)
        self.words[word_id] = word
        return word_id

    def record_sentence_ctx_changes(self, ctx: SentenceCtx):
        pass


def replace_ee(text: str) -> str:
    text = text.replace("ё", "е")
    return text


@dataclasses.dataclass
class DerivativeForm:
    form: str
    initial_form: str
    part_of_speech: PartOfSpeech

    @staticmethod
    def create(word: str):
        parse_results = morph.parse(word)
        if parse_results:
            form = parse_results[0]
            initial_form = form.normal_form
            part_of_speech = PartOfSpeech.from_pymorphy_str(form.tag.POS)
            derivative_form = DerivativeForm(word, initial_form, part_of_speech)

            return derivative_form
        return None


def test_derivative_form():
    form = DerivativeForm.create("Летчик")
    print(form)


def test_ctx():
    text = "Летчик пилотировал самолет боковой ручкой управления в плохую погоду. Мама мыла Милу мылом."
    text_ctx = TextCtx()
    text_ctx.init_for_text(text)

    sentence1 = text_ctx.start_sentence_edit(10)
    sentence1.add_collocation([0, 1, 2], LingKind.OBJECT)
    sentence1.mark_text_part(20, 40, LingKind.PREDICATE)
    html = sentence1.get_funny_html()
    print(html)
    pass


if __name__ == "__main__":
    test_derivative_form()
    # test_ctx()
