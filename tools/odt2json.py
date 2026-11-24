#!/usr/bin/env python3
"""Convert an .odt file into a Joread story JSON chunk.

Usage:
    python3 tools/odt2json.py path/to/Unbounced.odt [--images-dir images] [--title "My Story"] [--author "Author"]

Prints a single story JSON object to stdout. Append it to the "stories" array in stories.json.

The converter:
  1. Reads content.xml inside the .odt ZIP.
  2. Extracts each paragraph / heading as a "text" block, in document order.
  3. Copies each embedded image from Pictures/ into --images-dir with a sanitized filename.
  4. Emits an "image" block per picture, inline where it appears.

Requires only the Python standard library (zipfile, xml.etree.ElementTree).
"""
import os
import re
import json
import zipfile
import argparse
import xml.etree.ElementTree as ET

OFFICE_NS = "urn:oasis:names:tc:opendocument:xmlns:office:1.0"
TEXT_NS = "urn:oasis:names:tc:opendocument:xmlns:text:1.0"
DRAW_NS = "urn:oasis:names:tc:opendocument:xmlns:drawing:1.0"
XLINK_NS = "http://www.w3.org/1999/xlink"


def q(tag, ns):
    return "{%s}%s" % (ns, tag)


def slugify(text):
    text = (text or "").lower().strip()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return re.sub(r"-+", "-", text).strip("-") or "story"


def convert(odt_path, images_dir, title, author):
    images_dir = os.path.abspath(images_dir)
    os.makedirs(images_dir, exist_ok=True)

    used_names = {}

    def copy_image(href):
        name = href
        if name.startswith("./"):
            name = name[2:]
        basename = os.path.basename(name)
        if not basename:
            basename = "image.png"
        basename = re.sub(r"[^a-zA-Z0-9._-]", "_", basename)

        stem, ext = os.path.splitext(basename)
        candidate = basename
        i = 1
        while candidate in used_names or os.path.exists(os.path.join(images_dir, candidate)):
            candidate = "%s-%d%s" % (stem, i, ext)
            i += 1
        used_names[candidate] = True

        dest = os.path.join(images_dir, candidate)
        data = zf.read(name)
        with open(dest, "wb") as f:
            f.write(data)
        return "images/" + candidate

    zf = zipfile.ZipFile(odt_path)
    content = zf.read("content.xml")
    root = ET.fromstring(content)

    office_body = root.find(q("body", OFFICE_NS))
    if office_body is None:
        raise SystemExit("Could not find office:body in content.xml")
    office_text = office_body.find(q("text", OFFICE_NS))
    if office_text is None:
        raise SystemExit("Could not find office:text in content.xml")

    blocks = []

    def paragraph_blocks(elem):
        """Merge a paragraph's text runs into one text block, emitting inline images in place."""
        out = []
        buf = []

        def flush():
            nonlocal buf
            t = "".join(buf).strip()
            buf = []
            if t:
                out.append({"type": "text", "content": t})

        def walk(el):
            if el.text:
                buf.append(el.text)
            for child in el:
                tag = child.tag
                if tag == q("frame", DRAW_NS):
                    flush()
                    img = child.find(q("image", DRAW_NS))
                    if img is not None:
                        href = img.get(q("href", XLINK_NS))
                        if href and href.startswith("Pictures/"):
                            src = copy_image(href)
                            alt = img.get(q("name", DRAW_NS)) or ""
                            out.append({"type": "image", "src": src, "alt": alt, "caption": ""})
                else:
                    walk(child)
                if child.tail:
                    buf.append(child.tail)

        walk(elem)
        flush()
        return out

    for child in office_text:
        tag = child.tag
        if tag == q("p", TEXT_NS) or tag == q("h", TEXT_NS):
            blocks.extend(paragraph_blocks(child))
        elif tag == q("frame", DRAW_NS):
            img = child.find(q("image", DRAW_NS))
            if img is not None:
                href = img.get(q("href", XLINK_NS))
                if href and href.startswith("Pictures/"):
                    src = copy_image(href)
                    alt = img.get(q("name", DRAW_NS)) or ""
                    blocks.append({"type": "image", "src": src, "alt": alt, "caption": ""})

    story_id = slugify(title) or "untitled-story"
    story = {
        "id": story_id,
        "title": title or "Untitled Story",
    }
    if author:
        story["author"] = author
    story["blocks"] = blocks
    return story


def main():
    ap = argparse.ArgumentParser(description="Convert .odt to Joread story JSON")
    ap.add_argument("odt", help="Path to .odt file")
    ap.add_argument("--images-dir", default="images", help="Directory to extract images into (default: images)")
    ap.add_argument("--title", default="", help="Story title (default: derived from filename)")
    ap.add_argument("--author", default="", help="Story author (optional)")
    args = ap.parse_args()

    if not args.title:
        args.title = os.path.splitext(os.path.basename(args.odt))[0]

    story = convert(args.odt, args.images_dir, args.title, args.author)
    print(json.dumps(story, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
