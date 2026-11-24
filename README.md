# Joread

A small, mobile-friendly web reader for short stories. Each story can interleave text and images. Built to read text extracted from `.odt` files (or typed by hand) into a single `stories.json`.

## Files

| File | Purpose |
|------|---------|
| `index.html` | Page structure, styling, and reader logic |
| `stories.json` | All stories, titles, text blocks, and image references |
| `images/` | Story images (extracted from `.odt` or added by hand) |
| `tools/odt2json.py` | Convert an `.odt` file into a story JSON block |

## Run locally

Browsers block loading `stories.json` when you open `index.html` by double-clicking it. Start a local server instead:

```bash
python3 -m http.server
```

Then open <http://localhost:8000>.

## Publish with GitHub Pages

1. Push these files to a GitHub repository.
2. In the repository, go to **Settings → Pages**.
3. Under **Build and deployment**, choose **Deploy from a branch**, select `main` and `/ (root)`, and save.

## Data format (`stories.json`)

```json
{
  "title": "Joread",
  "subtitle": "Short stories",
  "stories": [
    {
      "id": "the-monk-and-the-thief",
      "title": "The Monk and the Thief",
      "author": "Aesop",
      "blocks": [
        { "type": "text",  "content": "A monk was walking along the road..." },
        { "type": "image", "src": "images/monk-thief-01.jpg", "alt": "A monk meeting a thief", "caption": "The thief confesses." },
        { "type": "text",  "content": "He met a thief who said..." }
      ]
    }
  ]
}
```

Each story has an `id`, `title`, optional `author`, and a `blocks` array. Block types:

- `text` — a paragraph of story text (`content`)
- `image` — an image with `src` (relative to repo root), `alt`, and optional `caption`

To add or fix a story, edit `stories.json`; no code changes are needed.

## Import from `.odt` (Unbounced.odt, etc.)

The converter pulls text paragraphs and embedded images out of an `.odt` file and prints a story JSON object you can append to `stories.json`.

```bash
python3 tools/odt2json.py /home/mark/Downloads/Unbounced.odt --images-dir images --title "My Story"
```

This:

1. Reads `content.xml` inside the `.odt` ZIP.
2. Extracts each paragraph / heading as a `text` block, in document order.
3. Copies each embedded image from `Pictures/` into `images/` with a sanitized filename.
4. Emits an `image` block per picture, inline where it appears.

Copy the printed JSON into the `stories` array in `stories.json` (add a comma after the previous entry). Images land in `images/` and are referenced as `images/<filename>`.

## GitHub Pages + images

`images/` is served as static assets. Relative paths like `images/foo.jpg` work both locally and on GitHub Pages.

> **Before making this repository public:** confirm you have permission to republish any text or images you import from `.odt` files or other sources. Keep the repository private if unsure.

## Notes

- The reader remembers your last story using `localStorage` (`joread-last-story`).
- One language only (no bilingual toggle).
- No flame / lamp graphic.
- No external dependencies, no build step — static files only.
