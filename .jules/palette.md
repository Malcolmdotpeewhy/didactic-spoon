## 2024-05-15 - Missing hover affordances on buttons
**Learning:** In CustomTkinter applications, custom `CTkButton` components and elements acting as buttons often lack standard hover affordances. Without `cursor="hand2"`, users don't get immediate feedback that an element is clickable, leading to poor accessibility.
**Action:** Always apply `cursor="hand2"` to interactive elements to ensure clear click/drag usability.
## 2024-03-28 - CTkOptionMenu Affordances
**Learning:** In CustomTkinter, `CTkOptionMenu` components (dropdowns) do not automatically provide a change in the cursor (e.g., to a pointing hand) when hovered, unlike standard web buttons or links. This omission can make it slightly less obvious that the element is clickable and interactive, particularly when styled to blend into the application background.
**Action:** Always ensure `cursor="hand2"` is explicitly passed to `CTkOptionMenu` instances alongside other interactive widgets like `CTkButton` to maintain clear affordance and consistent visual UX cues across the application.
