import timeit

setup = "phase = 'Lobby'"
stmt_list = "phase in ['Lobby', 'Matchmaking']"
stmt_tuple = "phase in ('Lobby', 'Matchmaking')"
stmt_set = "phase in {'Lobby', 'Matchmaking'}"

time_list = timeit.timeit(stmt_list, setup=setup, number=10000000)
time_tuple = timeit.timeit(stmt_tuple, setup=setup, number=10000000)
time_set = timeit.timeit(stmt_set, setup=setup, number=10000000)

print(f"List: {time_list:.4f}s")
print(f"Tuple: {time_tuple:.4f}s")
print(f"Set: {time_set:.4f}s")
