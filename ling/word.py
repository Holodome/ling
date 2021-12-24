import dataclasses
import pymorphy2
import typing
import functools


morph = pymorphy2.MorphAnalyzer()


POS_NONE = 0x0
POS_NOUN = 0x1  # существительное
POS_ADJ = 0x2  # прилагательное
POS_COMP = 0x3  # компаратив
POS_VERB = 0x4  # глагол
POS_PRT = 0x5  # причастие
POS_GRND = 0x6  # деепричастие
POS_NUMR = 0x7  # числительное
POS_NPRO = 0x8  # местоимение
POS_PRED = 0x9  # предикатив
POS_PREP = 0xA  # предлог
POS_CONJ = 0xB  # союз
POS_PRCL = 0xC  # частица
POS_INTJ = 0xD  # междометие
POS_ADVB = 0xE  # наречие


def pos_from_pymorphy_str(pm: str):
    pymorphy_to_pos_dict = {
        "NOUN": POS_NOUN,
        "ADJF": POS_ADJ,
        "ADJS": POS_ADJ,
        "COMP": POS_COMP,
        "VERB": POS_VERB,
        "INFN": POS_VERB,
        "PRTF": POS_PRT,
        "PRTS": POS_PRT,
        "GRND": POS_GRND,
        "NUMR": POS_NUMR,
        "ADVB": POS_ADVB,
        "NPRO": POS_NPRO,
        "PRED": POS_PRED,
        "PREP": POS_PREP,
        "CONJ": POS_CONJ,
        "PRCL": POS_PRCL,
        "INTJ": POS_INTJ,
    }
    return pymorphy_to_pos_dict.get(pm, POS_.NONE)


def pos_to_russian(pos: int):
    lookup = [
        "",
        "существительное",
        "прилагательное",
        "компаратив",
        "глагол",
        "причастие",
        "деепричастие",
        "числительное",
        "местоимение",
        "предикатив",
        "предлог",
        "союз",
        "частица",
        "междометие",
        "наречие",
    ]
    return lookup[pos]


@dataclasses.dataclass(frozen=True)
class Word:
    word: str
    initial_form: typing.Union[str, None]
    part_of_speech: int


@functools.lru_cache(1024)
def analyse_word(word: str) -> typing.Union[Word, None]:
    if word.isnumeric():
        return Word(word, None, POS_NUMR)

    parse_results = morph.parse(word)
    if parse_results:
        form = parse_results[0]
        initial_form = form.normal_form
        # NOTE(hl): Because we don't do deep morphological analysis it is enough for us that text is equals
        # because the only other parameter we currently have is
        initial_form = initial_form if initial_form != word else None
        part_of_speech = pos_from_pymorphy_str(form.tag.POS)
        word = Word(word, initial_form, part_of_speech)
        return word