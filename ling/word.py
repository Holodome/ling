import dataclasses
import pymorphy2
import enum
import typing
import functools


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
        return pymorphy_to_pos_dict.get(pm, PartOfSpeech.NONE)


@dataclasses.dataclass(frozen=True)
class Word:
    word: str
    initial_form: typing.Union[str, None]
    part_of_speech: PartOfSpeech


@functools.lru_cache(1024)
def analyse_word(word: str) -> typing.Union[Word, None]:
    if word.isnumeric():
        return Word(word, None, PartOfSpeech.NUMR)

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