#!/usr/bin/python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""OnionHost site model, media ingest and static generation.

Shared by the wizard/dashboard editor (unprivileged, user space) and
by onionhost-publish (root, the only writer of the served tree).

Design contract (DESIGN-v2 SS5, DESIGN-v3 A7/A8/A17.1):
  * v1 tiers are exactly two: Simple Pages and Journal. Both are
    static under the hood: no database, no comments, no JavaScript
    required by the generated site, no user HTML (everything is
    escaped; the templates are fixed project files).
  * Slice 6B adds a third site kind, "app" (DESIGN-v3 A12/A20):
    an owner-installed application (a forum, a shop, any PHP
    program, or a native binary) served by the combined app
    container. An app model carries no pages/entries - the
    application owns its content in the app-data volume - only the
    title and the runtime ("php" | "native"). The publisher does
    not render anything for an app site; it provisions the slot
    and selects the app container (see onionhost-publish).
  * The site MODEL lives in the owner's home:
        ~/.config/onionhost/site.json
        ~/.config/onionhost/media/<sha256>.<ext>   (scrubbed photos)
    The model is the only thing the editor edits. Publishing renders
    a fresh static tree from the model; B never sees the model.
  * Timestamps are content-derived, never wall-clock: the publisher
    sets each served file's mtime to
        FIXED_EPOCH + (sha256(content) mod 10^8)
    and the Journal feed's <updated> values come from the same rule
    applied to each entry page's bytes, so ETag / Last-Modified /
    feed times leak neither edit times nor the owner's timezone.
  * Photos are scrubbed at INGEST (EXIF and all metadata stripped
    by re-encoding, orientation baked into the pixels first) and
    re-scrubbed by the publisher, which treats the user-space media
    store as untrusted input.
"""
import hashlib
import html
import json
import os
import re
import tempfile
from datetime import datetime, timezone

FIXED_EPOCH = 1577836800  # 2020-01-01T00:00:00Z; arbitrary fixed base
MAX_PHOTO_DIM = 1600      # px, longest side after ingest resize
MAX_PAGES = 8             # "a handful of pages" (Simple Pages tier)
MAX_ENTRIES = 500
MAX_TEXT = 20000          # chars per page/entry body
MAX_HEADING = 120
MAX_TITLE = 80

MODEL_VERSION = 1
_ID_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,31}$")
_MEDIA_RE = re.compile(r"^[0-9a-f]{64}\.(jpg|png)$")
_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

TEMPLATE_DIR = "/usr/lib/onionhost/templates"


def content_mtime(data):
    """The publisher timestamp rule (DESIGN-v3 A8)."""
    digest = int(hashlib.sha256(data).hexdigest(), 16)
    return FIXED_EPOCH + (digest % 100_000_000)


def rfc3339(ts):
    return datetime.fromtimestamp(ts, tz=timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%SZ")


# ------------------------------------------------------------------
# Model
# ------------------------------------------------------------------

def config_dir(home=None):
    return os.path.join(home or os.path.expanduser("~"),
                        ".config", "onionhost")


def model_path(home=None):
    return os.path.join(config_dir(home), "site.json")


def media_dir(home=None):
    return os.path.join(config_dir(home), "media")


def starter_model(tier, today=None, runtime="php", recipe=None):
    """Seed content for a fresh install (one welcome page / one
    first entry) so Go Live serves a real starter site. For the
    app kind there is no seed content - the owner's application
    is the content - only the runtime choice is recorded, plus
    optionally the id of a packaged recipe (A23) the platform
    should install into the slot for them; the key is omitted
    entirely for hand-installed apps, so existing models and
    backups are untouched by its existence."""
    today = today or datetime.now().strftime("%Y-%m-%d")
    if tier == "app":
        model = {
            "version": MODEL_VERSION,
            "tier": "app",
            "title": "My Website",
            "runtime": runtime,
            "pages": [],
            "entries": [],
        }
        if recipe:
            model["recipe"] = recipe
        return model
    if tier == "journal":
        return {
            "version": MODEL_VERSION,
            "tier": "journal",
            "title": "My Journal",
            "pages": [],
            "entries": [{
                "id": "e1",
                "date": today,
                "heading": "First entry",
                "text": "I set up my website today. More soon.",
                "photo": None,
            }],
        }
    return {
        "version": MODEL_VERSION,
        "tier": "pages",
        "title": "My Website",
        "pages": [{
            "id": "p1",
            "heading": "Welcome",
            "text": "This is my new website. I will write more "
                    "here soon.",
            "photo": None,
        }],
        "entries": [],
    }


def validate_model(model):
    """Raise ValueError on anything the publisher must not serve.
    The publisher re-validates; the editor validates before save."""
    if not isinstance(model, dict):
        raise ValueError("site model is not an object")
    if model.get("version") != MODEL_VERSION:
        raise ValueError("unsupported site model version")
    tier = model.get("tier")
    if tier not in ("pages", "journal", "app"):
        raise ValueError("unknown site tier: %r" % (tier,))
    title = model.get("title")
    if not isinstance(title, str) or not title.strip():
        raise ValueError("site title is empty")
    if len(title) > MAX_TITLE:
        raise ValueError("site title too long")
    pages = model.get("pages", [])
    entries = model.get("entries", [])
    if tier == "app":
        # An app site has no platform content: the application in
        # the app-data volume is the site. The model only records
        # which runtime the slot must provide.
        if model.get("runtime") not in ("php", "native"):
            raise ValueError("unknown app runtime: %r"
                             % (model.get("runtime"),))
        if pages or entries:
            raise ValueError("an app site cannot hold pages/entries")
        # Optional A23 recipe id: the packaged app the platform
        # installs and keeps updated for the owner. Sanity-checked
        # here (shape only - whether the recipe package is
        # installed is the applier's business, checked at publish).
        recipe = model.get("recipe")
        if recipe is not None and not (
                isinstance(recipe, str)
                and re.fullmatch(r"[a-z0-9][a-z0-9-]*", recipe)):
            raise ValueError("bad recipe id: %r" % (recipe,))
        return model
    if len(pages) > MAX_PAGES:
        raise ValueError("too many pages")
    if len(entries) > MAX_ENTRIES:
        raise ValueError("too many entries")
    seen = set()
    for item in list(pages) + list(entries):
        if not isinstance(item, dict):
            raise ValueError("site item is not an object")
        iid = item.get("id", "")
        if not _ID_RE.match(iid) or iid in seen:
            raise ValueError("bad or duplicate item id: %r" % iid)
        seen.add(iid)
        heading = item.get("heading", "")
        if not isinstance(heading, str) or not heading.strip():
            raise ValueError("item heading is empty")
        if len(heading) > MAX_HEADING:
            raise ValueError("item heading too long")
        text = item.get("text", "")
        if not isinstance(text, str) or len(text) > MAX_TEXT:
            raise ValueError("item text too long")
        photo = item.get("photo")
        if photo is not None and not _MEDIA_RE.match(photo or ""):
            raise ValueError("bad photo name: %r" % (photo,))
    for entry in entries:
        date = entry.get("date", "")
        if not _DATE_RE.match(date or ""):
            raise ValueError("bad entry date: %r" % (date,))
        # reject impossible dates like 2026-02-30
        datetime.strptime(date, "%Y-%m-%d")
    return model


def _scrub_text(value):
    """Remove stray tab / control characters from user text
    (slice 5A backstop): tabs become a single space, CR/CRLF
    normalise to LF, and every other C0 control character and DEL
    is dropped. Newlines are content (paragraph breaks) and stay."""
    if not isinstance(value, str):
        return value
    value = value.replace("\r\n", "\n").replace("\r", "\n")
    out = []
    for ch in value:
        if ch == "\t":
            out.append(" ")
        elif ch == "\n" or (ord(ch) >= 0x20 and ord(ch) != 0x7F):
            out.append(ch)
    return "".join(out)


def sanitize_model(model):
    """In-place _scrub_text over title, headings and body texts.
    Called on every save; the editor's in-memory model is cleaned
    too, so what the user sees after a save is what was stored."""
    if isinstance(model, dict):
        if isinstance(model.get("title"), str):
            model["title"] = _scrub_text(model["title"])
        items = list(model.get("pages", [])) + \
            list(model.get("entries", []))
        for item in items:
            if isinstance(item, dict):
                for key in ("heading", "text"):
                    if isinstance(item.get(key), str):
                        item[key] = _scrub_text(item[key])
    return model


def load_model(path):
    with open(path) as f:
        return validate_model(json.load(f))


def save_model(model, home=None):
    sanitize_model(model)
    validate_model(model)
    path = model_path(home)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=os.path.dirname(path),
                               prefix=".site-", suffix=".tmp")
    try:
        with os.fdopen(fd, "w") as f:
            json.dump(model, f, indent=1, sort_keys=True)
            f.write("\n")
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp, path)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise
    dfd = os.open(os.path.dirname(path), os.O_RDONLY)
    try:
        os.fsync(dfd)
    finally:
        os.close(dfd)


def next_id(model, prefix):
    used = {i["id"] for i in model.get("pages", []) +
            model.get("entries", [])}
    n = 1
    while "%s%d" % (prefix, n) in used:
        n += 1
    return "%s%d" % (prefix, n)


# ------------------------------------------------------------------
# Media ingest (scrub)
# ------------------------------------------------------------------

def scrub_image_bytes(src_path):
    """Re-encode an image with ALL metadata stripped. Returns
    (bytes, ext) where ext is 'jpg' or 'png'. Orientation from EXIF
    is baked into the pixels BEFORE the metadata is dropped, so
    phone photos still display the right way up. Raises on anything
    undecodable."""
    from PIL import Image, ImageOps  # local: host-only dependency
    with Image.open(src_path) as img:
        img = ImageOps.exif_transpose(img)
        keep_png = img.format == "PNG" or (
            img.mode in ("RGBA", "LA", "P"))
        # PIL carries source metadata in img.info (JPEG COM segment,
        # ICC profile, EXIF) and its encoders write info back out
        # unless told otherwise. Clearing it is what makes the
        # re-encode a scrub rather than a copy (measured: a serial
        # string in a COM segment otherwise survives intact).
        img.info = {}
        if img.width > MAX_PHOTO_DIM or img.height > MAX_PHOTO_DIM:
            img = img.copy()
            img.thumbnail((MAX_PHOTO_DIM, MAX_PHOTO_DIM),
                          Image.LANCZOS)
        import io
        buf = io.BytesIO()
        if keep_png:
            img.save(buf, format="PNG", optimize=True)
            return buf.getvalue(), "png"
        if img.mode not in ("RGB", "L"):
            img = img.convert("RGB")
        img.save(buf, format="JPEG", quality=88, optimize=True)
        return buf.getvalue(), "jpg"


def ingest_photo(src_path, home=None):
    """Copy a user-picked photo into the media store, scrubbed and
    content-named. Returns the media filename."""
    data, ext = scrub_image_bytes(src_path)
    name = "%s.%s" % (hashlib.sha256(data).hexdigest(), ext)
    mdir = media_dir(home)
    os.makedirs(mdir, exist_ok=True)
    dest = os.path.join(mdir, name)
    if not os.path.exists(dest):
        fd, tmp = tempfile.mkstemp(dir=mdir, prefix=".ingest-")
        try:
            with os.fdopen(fd, "wb") as f:
                f.write(data)
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp, dest)
        except BaseException:
            try:
                os.unlink(tmp)
            except OSError:
                pass
            raise
    return name


# ------------------------------------------------------------------
# Rendering (fixed project templates; everything escaped)
# ------------------------------------------------------------------

def _template(name):
    with open(os.path.join(TEMPLATE_DIR, name)) as f:
        return f.read()


def _fill(tmpl, **subs):
    out = tmpl
    for key, value in subs.items():
        out = out.replace("%%" + key + "%%", value)
    return out


def _paragraphs(text):
    parts = [p.strip() for p in re.split(r"\n\s*\n", text.strip())]
    out = []
    for part in parts:
        if not part:
            continue
        out.append("<p>%s</p>" %
                   html.escape(part).replace("\n", "<br>\n"))
    return "\n".join(out)


def _photo_block(photo, alt):
    if not photo:
        return ""
    return ('<p><img src="media/%s" alt="%s"></p>' %
            (photo, html.escape(alt, quote=True)))


def render_site(model, mdir, out_dir):
    """Render the full static tree into out_dir (which must exist
    and be empty). Returns the list of relative file paths written.
    Media files are copied verbatim here; the publisher re-scrubs
    them before the tree is served."""
    validate_model(model)
    if model["tier"] == "app":
        raise ValueError("app sites are not rendered; the "
                         "application in the app-data volume is "
                         "the site (onionhost-publish provisions "
                         "the slot instead)")
    os.makedirs(os.path.join(out_dir, "media"), exist_ok=True)
    written = []

    def write(rel, text):
        path = os.path.join(out_dir, rel)
        with open(path, "w") as f:
            f.write(text)
        written.append(rel)

    write("style.css", _template("style.css"))
    used_media = set()

    def copy_media(photo):
        if photo and photo not in used_media:
            used_media.add(photo)
            src = os.path.join(mdir, photo)
            with open(src, "rb") as f:
                data = f.read()
            with open(os.path.join(out_dir, "media", photo),
                      "wb") as f:
                f.write(data)
            written.append("media/" + photo)

    tier = model["tier"]
    title = html.escape(model["title"])
    if tier == "pages":
        items = []
        for page in model["pages"]:
            copy_media(page.get("photo"))
            body = (_photo_block(page.get("photo"),
                                 page["heading"]) +
                    _paragraphs(page["text"]))
            write("page-%s.html" % page["id"], _fill(
                _template("page.html"),
                TITLE=title, HEADING=html.escape(page["heading"]),
                BODY=body))
            items.append('<li><a href="page-%s.html">%s</a></li>' %
                         (page["id"], html.escape(page["heading"])))
        write("index.html", _fill(
            _template("index-pages.html"), TITLE=title,
            ITEMS="\n".join(items) or "<li>No pages yet.</li>"))
    else:
        indexed = list(enumerate(model["entries"]))
        indexed.sort(key=lambda t: (t[1]["date"], t[0]),
                     reverse=True)
        entries = [e for _, e in indexed]
        items = []
        feed_entries = []
        for entry in entries:
            copy_media(entry.get("photo"))
            body = (_photo_block(entry.get("photo"),
                                 entry["heading"]) +
                    _paragraphs(entry["text"]))
            page_text = _fill(
                _template("entry.html"), TITLE=title,
                HEADING=html.escape(entry["heading"]),
                DATE=html.escape(entry["date"]), BODY=body)
            write("entry-%s.html" % entry["id"], page_text)
            # Feed timestamps are content-derived (A17.1): the rule
            # applied to the entry page's own bytes. Never the
            # wall clock, never the owner's timezone.
            updated = rfc3339(content_mtime(page_text.encode()))
            items.append(
                '<li><a href="entry-%s.html">%s</a> '
                '<span class="date">%s</span></li>' %
                (entry["id"], html.escape(entry["heading"]),
                 html.escape(entry["date"])))
            summary = html.escape(
                entry["text"].strip().split("\n")[0][:200])
            feed_entries.append(_fill(
                _template("feed-entry.xml"),
                ID=entry["id"], HEADING=html.escape(entry["heading"]),
                UPDATED=updated, SUMMARY=summary))
        feed_updated = rfc3339(content_mtime(
            "".join(feed_entries).encode() or b"empty"))
        write("index.html", _fill(
            _template("index-journal.html"), TITLE=title,
            ITEMS="\n".join(items) or "<li>No entries yet.</li>"))
        write("feed.xml", _fill(
            _template("feed.xml"), TITLE=title,
            UPDATED=feed_updated, ENTRIES="\n".join(feed_entries)))
    return written
