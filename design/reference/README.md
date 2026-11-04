# Design reference: EasyUI components (raw collection)

`raw/` holds the component code and notes collected by hand from easyui.site (MIT licence), pasted batch by batch in the order received. These files are reference material only and are not imported by the app. The adapted components live in `web/src/components/ui/` (each file says what was changed and fixed); the licence notice is in `THIRD_PARTY_NOTICES.md`. Not reused: command-menu (it copied an install command to the clipboard and opened GitHub), not-found, magnetic-button, glass-navbar.

| File | Content |
|---|---|
| `01_index_globals_batch1_buttons.md` | component index, globals, button, press-button, magnetic-button, split-button |
| `02_globals_batch1_charts.md` | globals G1-G5, interactive-area-chart, bar-chart, live-line-chart |
| `03_batch2.md` | stat-card, animated-number, torque-dial |
| `04_batch3.md` | glass-navbar, animated-tabs, sheet, command-menu, combobox |
| `05_batch4.md` | spring-select, date-picker, calendar, stretch-switch, animated-file-upload, stepper |
| `06_batch5.md` | alert, notification-stack, skeleton, loader, directional-tooltip |
| `07_batch6.md` | advanced-data-table, smooth-accordion, badge, not-found |
| `08_earnings_activity_heatmap.md` | earnings, activity-heatmap (replace any earlier partial entries) |

Not shown on the site and written in this repo (`web/src/lib/`): `lib/utils` (cn), `lib/motion-tokens` (plus springMorph, springResponsive), `lib/chart-primitives`, `lib/dashboard-chart-utils`, the `--shadow-elevated` token.
