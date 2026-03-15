import timeit
import random

# Generate dummy commands
commands = []
words = ["Launch", "Dashboard", "Clear", "Cache", "Settings", "Profile", "Game", "Client", "Exit", "Reload", "Toggle", "Theme"]
for i in range(10000):
    title = f"{random.choice(words)} {random.choice(words)} {i}"
    subtitle = f"Description for {title}"
    commands.append({"title": title, "subtitle": subtitle, "action": lambda: None})

class DummyOmnibar:
    def __init__(self):
        self._all_commands = commands
        self._filtered_commands = []
        self._selected_index = 0

    def _render_results(self):
        pass

    def _filter_results_old(self, query):
        if not query:
            self._filtered_commands = self._all_commands[:]
        else:
            self._filtered_commands = []
            for cmd in self._all_commands:
                search_target = f"{cmd.get('title', '')} {cmd.get('subtitle', '')}".lower()
                if query in search_target:
                    self._filtered_commands.append(cmd)

            self._filtered_commands.sort(key=lambda c: 0 if c.get("title", "").lower().startswith(query) else 1)

        self._selected_index = 0
        self._render_results()

    def _filter_results_new(self, query):
        if not query:
            self._filtered_commands = self._all_commands[:]
        else:
            exact_matches = []
            other_matches = []

            for cmd in self._all_commands:
                title = cmd.get("title", "")

                # Precompute search_target exactly like original, but deferring title.lower() until necessary
                search_target = f"{title} {cmd.get('subtitle', '')}".lower()

                if query in search_target:
                    # We found a match! Does it start exactly with the query?
                    if title.lower().startswith(query):
                        exact_matches.append(cmd)
                    else:
                        other_matches.append(cmd)

            self._filtered_commands = exact_matches + other_matches

        self._selected_index = 0
        self._render_results()

omnibar = DummyOmnibar()
query = "launch"

t_old = timeit.timeit(lambda: omnibar._filter_results_old(query), number=100)
print(f"Old approach: {t_old:.4f} seconds")

t_new = timeit.timeit(lambda: omnibar._filter_results_new(query), number=100)
print(f"New approach: {t_new:.4f} seconds")

old_results = omnibar._filter_results_old(query)
old_filtered = omnibar._filtered_commands.copy()

new_results = omnibar._filter_results_new(query)
new_filtered = omnibar._filtered_commands.copy()

print(f"Both methods yield the same length: {len(old_filtered) == len(new_filtered)}")
print(f"Both methods yield the exact same elements: {old_filtered == new_filtered}")
