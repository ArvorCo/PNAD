# Session Context

## User Prompts

### Prompt 1

In ~/arvor/PNAD, docs/index.html fails 29 WCAG AA contrast checks. This predates the Datafolha 08/2026 second-layer work (verified: `git show HEAD~1:docs/index.html` also reports 29).

Reproduce:
  python3 -m http.server 8899 --directory docs &
  python3 scripts/contrast-audit.py http://localhost:8899/index.html

Failures cluster in: `a.tag primary` (17), `span.featured-flag` (7), `p.ficha-date` (2), `p.colophon` (1), `span.stamp inferencia` (1), one bare `span`. Several report color == backgrou...

