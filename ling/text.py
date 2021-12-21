import logging

from ling.session import Session

SENTENCE_END_MARKERS = ".!?"


class Text:
    def __init__(self, session: Session, text: str):
        self.session: Session = session
        self.text: str = text

        sentences = []
        sentence_start_idxs = []
        sentence_start_idx = 0
        for cursor, symb in enumerate(text + "\0"):
            if symb in SENTENCE_END_MARKERS or symb == "\0":
                sent_text = text[sentence_start_idx:cursor]
                sent_text = " ".join(sent_text.strip().split())
                sentences.append(sent_text)
                sentence_start_idxs.append(sentence_start_idx)
                sentence_start_idx = cursor + 1

        self.sentences = sentences
        self.sentence_start_idxs = sentence_start_idxs

    def get_sentence_idx_for_cursor(self, cursor: int) -> int:
        """Returns sentence index, in which cursor is located from given cursor"""
        if not self.sentences:
            logging.warning("Text object is not initialized with text")
            return -1

        result = len(self.sentences) - 1
        for idx in range(len(self.sentences) - 1):
            start = self.sentence_start_idxs[idx]
            next_start = self.sentence_start_idxs[idx + 1]
            if start <= cursor < next_start:
                result = idx
                break
        return result
