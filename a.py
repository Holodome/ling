import copy
import random


def test1(mat_init):
    mat = copy.deepcopy(mat_init)
    rows = len(mat)
    cols = len(mat[0])
    items_to_visit = []
    precomputed_row = ['#'] * cols

    for y in range(rows):
        for x in range(cols):
            if mat[y][x].isupper():
                items_to_visit.append((y, x))

    for y, x in items_to_visit:
        mat[y] = precomputed_row.copy()
        for row in range(rows):
            mat[row][x] = '#'
    return mat


def test2(mat_init):
    mat = copy.deepcopy(mat_init)
    rows = len(mat)
    cols = len(mat[0])
    queue = []
    for i in range(rows):
        now = False
        for j in range(cols):
            if mat[i][j].isupper():
                now = True
                queue.append(j)
        if now:
            mat[i] = ['#'] * cols
    for j in queue:
        for i in range(0, rows):  # in queue?
            mat[i][j] = '#'
    return mat


def test3(mat_init):
    mat = copy.deepcopy(mat_init)
    rows = len(mat)
    cols = len(mat[0])
    for i, row in enumerate(mat):
        is_to_mark = False
        for j, it in enumerate(row):
            if it.isupper():
                is_to_mark = True
                if i != rows - 1 and mat[i + 1][j].islower():
                    mat[i + 1][j] = ""
                    for i_ in range(i):
                        mat[i_][j] = "#"
            elif it == "":
                row[j] = "#"
                if i != rows - 1 and mat[i + 1][j].islower():
                    mat[i + 1][j] = ""
        if is_to_mark:
            row[:] = ['#'] * cols
    return mat


MAT = [
    ["1", "2", "3", "3"],
    ["a", "B", "0", "B"],
    ["0", "d", "f", "9"],
    ["0", "d", "f", "f"],
]


import timeit
times = 100
tt1 = tt2 = tt3 = 0
m = 50
n = 50
for _ in range(times):
    mat = [[chr(random.randrange(1, 256)) for _ in range(m)] for _ in range(n)]
    tt1 += timeit.timeit(lambda: test1(mat), number=100)
    tt2 += timeit.timeit(lambda: test2(mat), number=100)
    tt3 += timeit.timeit(lambda: test3(mat), number=100)
print(tt1 / times)
print(tt2 / times)
print(tt3 / times)

# for _ in range(100):
#     m = 100
#     n = 100
#     mat = [[chr(random.randrange(1, 256)) for _ in range(m)] for _ in range(n)]
#     r1 = test1(mat)
#     r2 = test2(mat)
#     r3 = test3(mat)
#
#     for row in range(n):
#         assert r1[row] == r2[row] == r3[row]