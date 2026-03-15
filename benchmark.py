import timeit

list_code = """
roles = ["top", "jungle", "middle", "bottom", "utility", "fill"]
for r_name in roles:
    pass
"""

tuple_code = """
roles = ("top", "jungle", "middle", "bottom", "utility", "fill")
for r_name in roles:
    pass
"""

print("List benchmark:", timeit.timeit(list_code, number=10000000))
print("Tuple benchmark:", timeit.timeit(tuple_code, number=10000000))
