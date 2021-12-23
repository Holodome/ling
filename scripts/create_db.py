import traceback
import sys

sys.path.append("../ling")
import ling.session
import ling.sentence


db_name = "test.sqlite"

try:
    session = ling.session.Session()
    session.init_for_db(db_name)
    db = session.db
    predicate = db.add_sg("Предикат")
    object_ = db.add_sg("Объект")
    agent = db.add_sg("Агент")
    instrument = db.add_sg("Инструмент")
    locative = db.add_sg("Локатив")
    weather = db.add_sg("Погодные условия")
    height = db.add_sg("Высота")
    regime = db.add_sg("Режим")
    angle = db.add_sg("Угол наклона")
    speed = db.add_sg("Скорость")
    
    sentence = ling.sentence.Sentence(session,
        "Лётчик пилотировал самолет боковой ручкой управления на аэродроме с нежестким покрытием в плохую погоду.")
    sentence.make_col([0], agent)
    sentence.make_col([1], predicate)
    sentence.make_col([2], object_)
    sentence.make_col([3, 4, 5, 6], instrument)
    sentence.make_col([7, 8, 9, 10, 11], locative)
    sentence.make_col([12, 13], weather)
    sentence.make_default_cons()
    db.add_or_update_sentence_record(sentence)

    sentence = ling.sentence.Sentence(session,
        "Робот пилотировал корабль на базу «Север».")
    sentence.make_col([0], agent)
    sentence.make_col([1], predicate)
    sentence.make_col([2], object_)
    sentence.make_col([3, 4, 5], locative)
    sentence.make_default_cons()
    db.add_or_update_sentence_record(sentence)

    sentence = ling.sentence.Sentence(session,
        "Пилотировать самолёт, строго придерживаясь зоны пилотирования.")
    sentence.make_col([0], predicate)
    sentence.make_col([1], agent)
    sentence.make_col([4, 5], locative)
    sentence.make_default_cons()
    db.add_or_update_sentence_record(sentence)

    sentence = ling.sentence.Sentence(session,
                                      "Независимо от метеоусловий и видимости производить фигуры высшего пилотажа на высоте 13.000 фунтов.")
    sentence.make_col([0, 1, 2, 3, 4], weather)
    sentence.make_col([5], predicate)
    sentence.make_col([6, 7, 8], object_)
    sentence.make_col([9, 10, 11, 12], height)
    sentence.make_default_cons()
    db.add_or_update_sentence_record(sentence)

    sentence = ling.sentence.Sentence(session,
        "Взлёт производить на взлётном режиме работы двигателей с закрылками, выпущенными на 20° и 10°.");
    sentence.make_col([0], object_)
    sentence.make_col([1], predicate)
    sentence.make_col([3, 4, 5, 6, 7, 8], regime)
    sentence.make_col([11, 12, 13], angle)
    sentence.make_default_cons()
    db.add_or_update_sentence_record(sentence)

    sentence = ling.sentence.Sentence(session,
                                      "Дальнейший полёт производить на скорости 380-420 км/ч на высоте ближайшего эшелона.")
    sentence.make_col([0, 1], object_)
    sentence.make_col([2], predicate)
    sentence.make_col([4, 5, 6, 7, 8], speed)
    sentence.make_col([10, 11, 12], height)
    sentence.make_default_cons()
    db.add_or_update_sentence_record(sentence)
except Exception:
    traceback.print_exc()
