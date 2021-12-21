from ling.db import *
import traceback


def make_def_conns(pred_id, ctx):
    found_predicate_idx = -1
    for i, col in enumerate(ctx.collocations):
        if col.semantic_group == pred_id:
            found_predicate_idx = i
            break
    if found_predicate_idx != -1:
        for i, col in enumerate(ctx.collocations):
            if i == found_predicate_idx or col.semantic_group == pred_id:
                continue

            ctx.make_connection(pred_id, i)


db_name = "test.sqlite"

try:
    ctx = DBCtx()
    ctx.create_or_open(db_name)

    predicate = ctx.add_semantic_group("Предикат")
    object_ = ctx.add_semantic_group("Объект")
    agent = ctx.add_semantic_group("Агент")
    instrument = ctx.add_semantic_group("Инструмент")
    locative = ctx.add_semantic_group("Локатив")
    weather = ctx.add_semantic_group("Погодные условия")
    height = ctx.add_semantic_group("Высота")
    regime = ctx.add_semantic_group("Режим")
    angle = ctx.add_semantic_group("Угол наклона")
    speed = ctx.add_semantic_group("Скорость")

    sentence = ling.SentenceCtx()
    sentence.init_from_text(
        "Лётчик пилотировал самолет боковой ручкой управления на аэродроме с нежестким покрытием в плохую погоду.")
    sentence.mark_words([0], agent)
    sentence.mark_words([1], predicate)
    sentence.mark_words([2], object_)
    sentence.mark_words([3, 4, 5, 6], instrument)
    sentence.mark_words([7, 8, 9, 10, 11], locative)
    sentence.mark_words([12, 13], weather)
    make_def_conns(predicate, sentence)
    ctx.add_or_update_sentence_record(sentence)

    sentence.init_from_text("Робот пилотировал корабль на базу «Север».")
    sentence.mark_words([0], agent)
    sentence.mark_words([1], predicate)
    sentence.mark_words([2], object_)
    sentence.mark_words([3, 4, 5], locative)
    make_def_conns(predicate, sentence)
    ctx.add_or_update_sentence_record(sentence)

    sentence.init_from_text("Пилотировать самолёт, строго придерживаясь зоны пилотирования.")
    sentence.mark_words([0], predicate)
    sentence.mark_words([1], agent)
    # sentence.mark_words([2, 3, 4, 5], )
    make_def_conns(predicate, sentence)
    ctx.add_or_update_sentence_record(sentence)

    sentence.init_from_text(
        "Независимо от метеоусловий и видимости производить фигуры высшего пилотажа на высоте 13.000 фунтов.")
    sentence.mark_words([0, 1, 2, 3, 4], weather)
    sentence.mark_words([5], predicate)
    sentence.mark_words([6, 7, 8], object_)
    sentence.mark_words([9, 10, 11, 12], height)
    make_def_conns(predicate, sentence)
    ctx.add_or_update_sentence_record(sentence)

    sentence.init_from_text(
        "Взлёт производить на взлётном режиме работы двигателей с закрылками, выпущенными на 20° и 10°.");
    sentence.mark_words([0], object_)
    sentence.mark_words([1], predicate)
    sentence.mark_words([3, 4, 5, 6, 7, 8], regime)
    sentence.mark_words([11, 12, 13], angle)
    make_def_conns(predicate, sentence)
    ctx.add_or_update_sentence_record(sentence)

    sentence.init_from_text("Дальнейший полёт производить на скорости 380-420 км/ч на высоте ближайшего эшелона.")
    sentence.mark_words([0, 1], object_)
    sentence.mark_words([2], predicate)
    sentence.mark_words([4, 5, 6, 7, 8], speed)
    sentence.mark_words([10, 11, 12], height)
    make_def_conns(predicate, sentence)
    ctx.add_or_update_sentence_record(sentence)
except Exception:
    traceback.print_exc()