# Curie Web

SvelteKit frontend for the Curie project hub, auth pages, report workspace, resume overlay, and benchmark overlay.

## Main Routes

- `/`: project hub with Ampere, Bohr, and Curie architecture sections.
- `/curie`: authenticated reporting workspace and report cards.
- `/curie/login`: sign-in page.
- `/curie/register`: account creation page.
- `/curie/reports/[reportId]`: protected report iframe shell.

## Development

```bash
cd apps/web
npm install
npm run dev
```

Useful checks:

```bash
npm run format
npm run check
npm run lint
npm run build
```

## API Types

The app consumes generated types from `@curie/api-client`, backed by `packages/contracts/openapi.json`. Regenerate from the repository root after API schema changes:

```bash
bash scripts/export-openapi.sh
bash scripts/generate-api-client.sh
```

## Styling

Global SvelteKit styling lives in `src/app.css`. Project-owned CSS follows BEM:

- `curie-page`: page shell and layout helpers.
- `curie-card`: shared card block with modifiers such as `curie-card--clickable`.
- `curie-button`: shared action block with modifiers such as `curie-button--primary`.
- `curie-header`: Flowbite Navbar wrapper and menu elements.
- `project-flow`: Svelte Flow custom node and edge elements.
- `report-page`: report iframe and expanded report state.

Third-party selectors such as `.svelte-flow__*` remain vendor selectors and are documented in the CSS comments.
