# Frontend Styling

Curie uses global CSS for shared SvelteKit and Streamlit surfaces. Project-owned CSS follows BEM naming so blocks, elements, and modifiers are searchable and reusable.

## BEM Rules Used Here

- Blocks are standalone UI concepts, for example `curie-card`, `curie-button`, `curie-header`, `project-flow`, and `report-page`.
- Elements belong to a block, for example `curie-header__menu`, `project-flow__edge-label`, and `reporting-kpis__card`.
- Modifiers describe state or variants and are applied together with the base block or element, for example `curie-card curie-card--clickable` and `curie-header__menu-action curie-header__menu-action--selected`.
- Class selectors are preferred for project-owned CSS. Tag selectors are avoided for owned markup.

## SvelteKit CSS

The SvelteKit stylesheet is:

```text
apps/web/src/app.css
```

Main owned blocks:

- `curie-page`: shared page font and shell width.
- `curie-card`: shared card design with surface, clickable, intro, flat, static, and flow modifiers.
- `curie-button`: shared action buttons with icon and primary modifiers.
- `curie-header`: Flowbite Navbar wrapper, menu, submenu, and social links.
- `project-intro`: project cards on the home introduction section.
- `project-flow`: custom Svelte Flow node, group, title link, and edge styling.
- `report-page`: protected report iframe, loading cover, and expanded frame state.
- `curie-overlay`: modal and overlay blur treatment.

Third-party selectors such as `.svelte-flow__*` are kept because Svelte Flow owns that generated markup.

## Streamlit CSS

The Streamlit stylesheet is:

```text
apps/streamlit/styles/reporting.css
```

Owned Streamlit report markup uses the `reporting-kpis` block rendered from:

```text
apps/streamlit/shared/reporting_ui.py
```

Streamlit-generated selectors such as `[data-testid="stSidebar"]` are documented exceptions because Streamlit controls those DOM nodes.
