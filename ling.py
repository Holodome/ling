import enum
import dataclasses
from typing import List, DefaultDict
import re
from collections import defaultdict


class LingKind(enum.Enum):
    NONE = 0x0
    ADJUNCT = enum.auto()
    AGENT = enum.auto()
    PREDICATE = enum.auto()
    OBJECT = enum.auto()
    INSTRUMENT = enum.auto()
    # Новые типы идут ниже

    # Маркер окончания
    COUNT = enum.auto()


LING_KIND_STRINGS = [
    "Адъюнкт",
    "Агент",
    "Предикат",
    "Объект",
    "Инструмент"
]

assert len(LING_KIND_STRINGS) == LingKind.COUNT.value - 1

COLOR_TABLE = [
    "red",
    "blue",
    "green",
    "yellow",
    "cyan",
    "orange"
]


def get_parts_from_marks(text, marks):
    parts = [(text, LingKind.NONE)]
    # Algorithm pass
    for mark in marks:
        start, end, kind = mark
        assert end > start
        # find element that contains current mark
        # split that element into two groups
        # if end is not met, keep splitting or changing next elements
        parts_overlapped = []
        cursor = 0
        for i, part in enumerate(parts):
            if end > cursor and cursor + len(part[0]) >= start:
                parts_overlapped.append((i, cursor))
            cursor += len(part[0])
        print(parts_overlapped)

        new_parts = parts.copy()
        idx_advance = 0
        for i, (part_idx, part_start) in enumerate(parts_overlapped):
            part_idx += idx_advance
            part = new_parts[part_idx]
            part_text = part[0]
            local_idx_advance = 0
            if i == 0 == len(parts_overlapped) - 1:
                idx1 = start - part_start
                idx2 = end - part_start
                text0 = part_text[:idx1]
                text1 = part_text[idx1:idx2]
                text2 = part_text[idx2:]
                if text0:
                    new_parts.insert(part_idx + local_idx_advance, (text0, part[1]))
                    local_idx_advance += 1
                if text1:
                    new_parts.insert(part_idx + local_idx_advance, (text1, kind))
                    local_idx_advance += 1
                if text2:
                    new_parts.insert(part_idx + local_idx_advance, (text2, part[1]))
                    local_idx_advance += 1
                del new_parts[part_idx + local_idx_advance]
                local_idx_advance -= 1
            elif i == 0:
                idx_to_split = start - part_start
                text0 = part_text[:idx_to_split]
                text1 = part_text[idx_to_split:]
                if text0:
                    new_parts.insert(part_idx + local_idx_advance, (text0, part[1]))
                    local_idx_advance += 1
                if text1:
                    new_parts.insert(part_idx + local_idx_advance, (text1, kind))
                    local_idx_advance += 1
                del new_parts[part_idx + local_idx_advance]
                local_idx_advance -= 1
            # if it is the last
            elif i == len(parts_overlapped) - 1:
                idx_to_split = end - part_start
                text0 = part_text[:idx_to_split]
                text1 = part_text[idx_to_split:]
                if text0:
                    new_parts.insert(part_idx + local_idx_advance, (text0, kind))
                    local_idx_advance += 1
                if text1:
                    new_parts.insert(part_idx + local_idx_advance, (text1, part[1]))
                    local_idx_advance += 1
                del new_parts[part_idx + local_idx_advance]
                local_idx_advance -= 1
            elif 0 < i < len(parts_overlapped) - 1:
                new_parts[part_idx] = (part_text, kind)
            else:
                assert False
            idx_advance += local_idx_advance
        parts = new_parts

    # Optimization pass
    new_parts = []
    last_editable = None
    for i in range(len(parts)):
        if last_editable is None:
            last_editable = parts[i]
        elif last_editable[1] == parts[i][1]:
            last_editable = (last_editable[0] + parts[i][0], last_editable[1])
        else:
            new_parts.append(last_editable)
            last_editable = parts[i]
    if last_editable is not None:
        new_parts.append(last_editable)
    parts = new_parts
    return parts


def test():
    text = "abcdefgh"
    marks = [
        (1, 5, LingKind.AGENT),
        (5, 7, LingKind.ADJUNCT),
        (3, 6, LingKind.PREDICATE),
        (2, 6, LingKind.NONE)
    ]
    parts = get_parts_from_marks(text, marks)
    print(parts)
    exit(0)


class TextParseState:
    def __init__(self, text):
        self.text = text
        self.marks = []

        self.html_formatted_text = text
        self.mark_generation = 0
        self.last_parts = None
        self.last_parts_generation = None

    def get_parts_cached(self):
        if self.last_parts_generation is None or \
                self.last_parts_generation != self.mark_generation:
            self.last_parts = get_parts_from_marks(self.text, self.marks)

        return self.last_parts

    def regenerate_html(self):
        parts = self.get_parts_cached()
        html = ""
        for part in parts:
            part_html = part[0]
            if part[1] != LingKind.NONE:
                color = COLOR_TABLE[part[1].value - 1]
                part_html = f"<font color={color}>{part_html}</font>"
            html += part_html
        self.html_formatted_text = html

    def get_structured_output(self):
        result = [[] for _ in range(LingKind.COUNT.value)]
        parts = self.get_parts_cached()
        print(parts)
        for part in parts:
            idx = part[1].value
            result[idx].append(part[0])
        return parts

    def mark(self, sel_start, sel_end, kind):
        result = False
        # @TODO validate
        if sel_start != sel_end:
            self.mark_generation += 1
            mark = (sel_start, sel_end, kind)
            self.marks.append(mark)
            self.regenerate_html()
            result = True
        return result
