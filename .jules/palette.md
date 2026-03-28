## 2024-05-15 - Missing hover affordances on buttons
**Learning:** In CustomTkinter applications, custom `CTkButton` components and elements acting as buttons often lack standard hover affordances. Without `cursor="hand2"`, users don't get immediate feedback that an element is clickable, leading to poor accessibility.
**Action:** Always apply `cursor="hand2"` to interactive elements to ensure clear click/drag usability.
