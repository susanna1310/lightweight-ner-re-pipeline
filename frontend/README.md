# Clinical NER & RE Explorer — Frontend

A React single-page app for exploring named-entity recognition (NER) and relation-extraction (RE) results from clinical text. You upload a document (or plain text), pick one of the trained i2b2 models, and the app highlights the extracted entities inline and lets you inspect the relations between them.

This app is the UI only — it has no models or data of its own. It talks to the Flask API in [`../backend`](../backend/app.py), which loads the spaCy NER/RE models and does the actual inference.

## Prerequisites

- Node.js (a recent LTS version) and npm
- The backend running locally at `http://localhost:5000` (see `../backend/app.py`). Start it before using the app — every action (upload, model switch, threshold/label change) calls it.
- The trained model files the backend loads (see "Models" below). **Without them the backend process won't even start**, so the frontend will load fine but every action will fail (uploads/model switches just spin and then silently fail).

## Models

The i2b2/n2c2 NER and RE models used by the backend are **not included in this repository** — they're trained on clinical datasets (i2b2 2010/2012/2014, n2c2 2018) that require a signed Data Use Agreement, so the trained model artifacts can't be redistributed alongside the code.

`backend/app.py` expects them at:

- `re_models/re_model_2010/model-best` — "2010 Medical Relations"
- `re_models/re_model_2012/model-best` — "2012 Temporal-Relations"
- `re_models/re_model_2018/model-best` — "2018 ADE"
- `ner_models/ner_model_2014/model-best` — "2014 De-Identification"

If these directories are missing, `spacy.load(...)` at backend startup (and in `/api/model`) raises an error and the Flask process fails to come up, so anyone cloning this repo needs their own copies of these models (obtained under their own DUA) placed at those paths before the app is usable end-to-end.

## Getting started

```bash
npm install
npm start
```

Runs the app in development mode at [http://localhost:3000](http://localhost:3000). The page reloads on changes.

## Available scripts

- `npm start` — runs the dev server (`react-scripts start`).
- `npm run build` — builds a production bundle into `build/`.
- `npm run eject` — ejects the Create React App config (one-way, not expected to be needed).

There is no test suite in this project.

## How it works

1. **Upload** (`FileUpload`) — drop or select a `.pdf` or plain-text file. The app posts it to `POST /api/upload`, which returns the rendered HTML (entities wrapped in `<mark>` tags via spaCy's displaCy), the list of entity labels found, the raw text, and the extracted relations.
2. **Rendering** — `App.js` converts each displaCy `<mark>` into a clickable `<button>` (`convertMarkToButton`), tagging it with a stable `id` equal to the entity's index in the model's full entity list (not its position among whatever is currently rendered — see "Filtering" below for why that distinction matters).
3. **Model select** — switching models (`POST /api/model`) reruns the uploaded text through a different trained model and re-renders everything.
4. **Threshold select** — only relevant for relation-extraction models; refilters which relations count as "found" by confidence (`POST /api/threshold`).
5. **Label filter** — restricts which entity labels are highlighted/clickable in the text (`POST /api/filter`). This **only affects what's highlighted in the text** — see "Known behavior" below.
6. **Clicking an entity** opens the sidebar (`Sidebar.js`), showing an AG Grid table of that entity's relations (target entity, target's label, relation type, confidence value). Hovering a row highlights and scrolls to the corresponding target entity in the text.

The "2014 De-Identification" model has no relations and no threshold concept, so both the threshold selector and the relations sidebar are hidden when it's selected.

## Known behavior (by design)

- **The label filter does not filter the relations table.** If you filter the text to show only e.g. `PROBLEM` entities and then click one, the sidebar still shows *all* of that entity's relations, including ones pointing at entities of other labels (which may not currently be highlighted in the text). This is intentional: most relation types in these datasets connect entities of *different* labels (e.g. a `TREATMENT` related to a `PROBLEM`), so restricting the table to same-label targets would hide most or all relations for many entities.
- Relation rows always show the target entity's real text/label (returned directly by the backend), regardless of whether that target is currently rendered/highlighted in the text panel.

## Project structure

```
src/
  App.js                 # top-level state, API calls, entity<->button rendering
  App.css                # Tailwind entrypoint + small AG Grid overrides
  index.js                # CRA entrypoint
  components/
    FileUpload.js         # drag-and-drop / click-to-upload control
    Selector.js            # generic labeled <select> used for model/threshold/label
    Sidebar.js              # relations table (AG Grid) for the selected entity
```

## Configuration

The backend URL is a constant at the top of `src/App.js`:

```js
const API_BASE_URL = "http://localhost:5000"
```

There's no `.env` support for this yet — if the backend runs elsewhere, edit that constant.

## Styling

Tailwind CSS + [daisyUI](https://daisyui.com/) (see `tailwind.config.js`), using a custom `tum` theme. AG Grid (`ag-grid-community` / `ag-grid-react`) renders the relations table in the sidebar, styled with the `ag-theme-alpine` theme plus text-wrapping overrides in `App.css`.
