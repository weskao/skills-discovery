## [0.9.0] - 2026-06-09

### 🚀 Features

- **spec:** Add WebFetch fallback for star-count refresh
- **spec:** Darwin optimization — dim4 + dim9 (+7.8 pts)
## [0.8.0] - 2026-06-06

### 🚜 Refactor

- **registry:** [**breaking**] Remove version field and migration logic

### 📚 Documentation

- **changelog:** Release v0.8.0
## [0.7.0] - 2026-06-04

### 🚀 Features

- **registry:** [**breaking**] Enrich entries with date/star metadata

### 🐛 Bug Fixes

- **spec:** Fill metadata gaps for v1.0-migrated registry entries

### 📚 Documentation

- **changelog:** Release v0.7.0
## [0.6.0] - 2026-06-03

### 🚀 Features

- **registry:** Add hooks and workflows categories
- **skill:** [**breaking**] Add categories, delivery chain, name validation

### 📚 Documentation

- **readme:** Add hermes host to project-aware table
- **readme:** Update delivery options and add hermes examples
- Add maintainer guide with category invariant
- **changelog:** Release v0.6.0

### ⚙️ Miscellaneous Tasks

- Add category-sync guard and doc linting
- Add .source for copy-based installs
## [0.5.1] - 2026-05-28

### 🐛 Bug Fixes

- **discovery:** Make candidates merge append-only

### 📚 Documentation

- **changelog:** Release v0.5.1
## [0.5.0] - 2026-05-24

### 🚀 Features

- **discovery:** Add security category to skills and tools tracks

### 🚜 Refactor

- [**breaking**] Rename skill-discovery → skills-discovery

### 📚 Documentation

- **changelog:** Release v0.5.0
## [0.4.0] - 2026-05-22

### 🚀 Features

- **security:** Harden reply protocol against injection
- **discovery:** Add optional keyword arg to scope searches

### 📚 Documentation

- **changelog:** Release v0.4.0
## [0.3.0] - 2026-05-21

### 🚀 Features

- **discovery:** Self-healing bootstrap, installed-state diff, openclaw delivery

### 🐛 Bug Fixes

- **scoring:** Exempt multi-skill collection repos and add subagent topics

### 📚 Documentation

- **changelog:** Release v0.3.0
## [0.2.0] - 2026-05-19

### 🚀 Features

- **discovery:** Broaden GitHub search with more topics, skill_keywords, and awesome lists

### 📚 Documentation

- **readme:** Generalize recommended schedule for openclaw + other hosts
- **readme:** Adopt neon_counter style — emoji headings + features list
- **readme:** Add default categories table to Customization section
- **readme:** Document skill_keywords, add project-local install section, fix lint
- **skill:** Add hyperlinked skill names in Telegram report and Hermes install path
- **skill:** Document skill-candidates.yaml merge behavior
- **changelog:** Release v0.2.0
- **changelog:** Release v0.2.0
## [0.1.0] - 2026-05-17

### 🚀 Features

- Initial skill-discovery release
- Project-aware skill home (no more hardcoded .claude)

### 📚 Documentation

- **readme:** Add usage guide with tg_send caveat
- **license:** Add MIT license
- **readme:** Tighten project-aware section copy
- **changelog:** Release v0.1.0

### ⚙️ Miscellaneous Tasks

- Add .gitignore for macOS and Windows system files
