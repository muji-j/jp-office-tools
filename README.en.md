# jp-office-tools — General-Purpose Office Tools for Japanese Business Environments (Claude Code Plugin)

[日本語](README.md) | **English**

A collection of **general-purpose** skills and commands that support common tasks in Japanese office work: cleaning up and comparing Excel/CSV files, drafting business documents (議事録 minutes, 稟議書 approval requests), and calculating public holidays, business days, and Japanese era (和暦) dates.

> **General-purpose, public-information only**: this plugin is built entirely from general business knowledge and publicly available holiday data. It contains **no company-specific information whatsoever** (no company names, internal templates, or actual contract content). That said, in real use you will be handling **in-house data**, so you must always follow your organization's AI usage policy.

---

## What's Included

| Type | Description |
|---|---|
| **Skill** `jp-excel` | Character-encoding detection and conversion for Excel/CSV (Shift-JIS/CP932/UTF-8), normalization of full-width/half-width characters and era-based (和暦) dates, file comparison (diff — full sheet support for xlsx, sheet by sheet), cross-tabulation (pivot), and chart generation |
| **Skill** `jp-bizdoc` | Templates for meeting minutes, approval requests (稟議書), and reports; keigo (敬語, honorific language) proofreading for emails; slide outline drafting; business document translation; PDF reading/summarization/table extraction (save to CSV/Excel); detection of notation inconsistencies and glossary creation |
| **Skill** `jp-mail` | Drafting and replying to business emails, boilerplate phrasing (request / thanks / apology / reminder / report / decline, each across 3 formality levels), and scheduling coordination |
| **Skill** `jp-slides` | Presentation (`.pptx`) generation — a visual engine where each of the 16 themes has its own distinct modern design (bento-style dashboard, oversized poster, organic wave, dark glass, etc.), stats slides for showcasing KPIs/metrics, customizable accent color/font/light-dark variant, support for in-house brand templates, and gallery/overview output showing all themes at once |
| **Skill** `jp-dates` | Holiday determination, business-day arithmetic (N business days before/after), 和暦↔西暦 (Japanese era ↔ Gregorian calendar) conversion, and fiscal-year calculation |
| **Commands** | `/xl-clean` (Excel/CSV cleansing) · `/xl-diff` (diff comparison) · `/xl-pivot` (cross-tabulation) · `/xl-chart` (chart generation) · `/giji` (meeting minutes generation) · `/ringi` (approval-request drafting) · `/mail` (email drafting/replying) · `/keigo` (honorific-language proofreading) · `/slides` (slide generation) · `/pdf-table` (PDF table extraction) · `/glossary` (notation-inconsistency detection / glossary creation) · `/jp-office-setup` (environment check) |

---

## Prerequisites

- **Claude Code** (any of CLI / desktop / IDE extension)
- (Optional) **Python 3.10+** — required for `jp-excel` (Excel/CSV cleansing and diff), `jp-dates` (holiday/business-day/era calculations), `jp-bizdoc`'s PDF text extraction, and `jp-slides` (`.pptx` generation).
- **All of `jp-bizdoc`'s document-drafting features (meeting minutes, approval requests, reports, keigo proofreading, slide outlines, translation) work without Python.** Python is only required for the script-backed features listed above (including `jp-slides`'s actual `.pptx` generation).

---

## Installation (Claude Code)

Run the following inside Claude Code (this is a public marketplace, **no GitHub authentication required**):

```
/plugin marketplace add muji-j/jp-office-tools
/plugin install jp-office@jp-office-tools
```

- The first line registers this marketplace, and the second installs the plugin (you can also browse and select it from the `/plugin` menu).
- If Python or its libraries are missing, running `/jp-office-setup` will check your environment and guide you through installation.

### Updating

```
/plugin marketplace update
/plugin install jp-office@jp-office-tools
```

(Once the author bumps the version and publishes a new release, the commands above pull the latest. See `CHANGELOG.md` for what changed.)

### Auto-update (recommended)

You can make an already-installed environment **automatically update on startup** whenever a new version is published (auto-update is configured on each user's side). Enable it via either of the following:

- **Easy**: open `/plugin`, go to **Marketplaces tab → `jp-office-tools` → enable auto-update**.
- **Bulk via settings (auto-install + auto-update)**: add the following to your own `~/.claude/settings.json` (merge with existing settings):

  ```json
  {
    "extraKnownMarketplaces": {
      "jp-office-tools": {
        "source": { "source": "github", "repo": "muji-j/jp-office-tools" },
        "autoUpdate": true
      }
    },
    "enabledPlugins": {
      "jp-office@jp-office-tools": true
    }
  }
  ```

  → This alone makes **installation automatic** too, and from then on the plugin updates automatically on startup (you may sometimes see a prompt to `/reload-plugins` after an update).

> Note: on a public marketplace, the distributor cannot force updates on users — auto-update is a setting on the user's side. To enforce it organization-wide, configure the same content above in managed settings.

---

## Usage Examples

- `/xl-clean sales.csv` … detects the character encoding, then cleanses the file (normalizing full-width/half-width characters, 和暦 dates, and whitespace), outputting a renamed copy plus a report
- `/xl-pivot sales.csv` … even without specifying column names, it inspects the column structure to suggest grouping and aggregation columns, then outputs a cross-tabulation table and CSV
- `/xl-chart sales.csv` … suggests an x-axis, y-axis, and chart type from the column structure, and generates a line/bar/pie chart as PNG or HTML
- `/giji` … paste in meeting notes or a transcript, and it generates minutes organized by decisions and action items (owner and deadline)
- `/mail` … paste in a received email or describe what you need, and after confirming the relationship (external formal / external standard / internal) and tone, it drafts a reply or new email
- `/slides` … tell it something like "make slides for the monthly report," and it infers the structure (conclusion-first / narrative-progression / comparative-review) and theme, generating a `.pptx` from the built-in 16 themes (a precise path is also available for specifying theme, accent color, font, and in-house brand templates)
- `/pdf-table document.pdf` … displays tables from within a PDF as markdown tables; if there are many, you can also choose to save them to CSV or Excel (xlsx)
- `/glossary` … pass in a document, and it suggests unification for notation inconsistencies (e.g., サーバー/サーバ, Ｗｅｂ/Web) and drafts a glossary from frequently occurring terms
- Ask something like "what's 5 business days before the 10th of next month?" and the `jp-dates` skill is automatically invoked to answer with the actual date

---

## License

MIT License (see `LICENSE`).

## Disclaimer

Holiday data depends on a library (`jpholiday`), and institutional rules, document formats, and honorific-language conventions may change over time (this package reflects the state as of 2026-07). Before making any important decisions, please verify the latest information against your organization's own rules and official sources. When handling real data, follow your organization's AI usage policy.
