#!/usr/bin/python3
# SPDX-License-Identifier: GPL-3.0-or-later
"""OnionHost first-boot wizard + site editor + dashboard.

One Tk program, three modes:

  wizard (default)  The A10 state machine (source of truth:
      /var/lib/onionhost/state):
        S0  kiosk session: generate the 3-word login phrase,
            copy-to-paper + verify, commit via the helper (S0->S1).
        S1  wizard autostarts in the desktop and resumes: choose
            the site kind (Simple Pages / Journal / your own
            application - slice 6B), edit the starter site (or,
            for an application, read the install brief), Go Live
            (publish + helper S1->S2).
        S2  the wizard exits immediately and never appears again.
  --dashboard       The owner's home screen after setup: site
      title + kind, a status card fed by the probe (via the
      helper), and an Edit button reopening the editor. Runs only
      at state S2.

The editor edits the site MODEL (~/.config/onionhost/site.json +
media store, see sitegen.py) in user space. Publishing is the
only privileged step and goes ONLY through onionhost-wizard-helper
(`publish`), which runs onionhost-publish as root. This process
never runs as root and never writes the served tree.
"""
import json
import os
import random
import subprocess
import sys
import threading
from datetime import datetime

sys.path.insert(0, "/usr/lib/onionhost")
import phrasegen  # noqa: E402
import sitegen  # noqa: E402

STATE_FILE = "/var/lib/onionhost/state"
RESTORED_MARKER = "/var/lib/onionhost/restored"
HELPER = "/usr/local/bin/onionhost-wizard-helper"
PROGRESS_DIR = os.path.expanduser("~/.config/onionhost")
PROGRESS_FILE = os.path.join(PROGRESS_DIR, "wizard-progress.json")

FONTS = {
    "title": ("Sans", 24, "bold"),
    "body": ("Sans", 14),
    "word": ("Monospace", 30, "bold"),
    "btn": ("Sans", 14, "bold"),
}


def read_state():
    try:
        with open(STATE_FILE) as f:
            return f.read().strip()
    except OSError:
        return None


def read_restored_onion():
    """The .onion address a Maintenance restore brought back, or
    None. onionhost-restore writes the marker only when setup had
    not finished (state S0); the wizard then offers the finishing
    page below instead of the fresh-site flow."""
    if read_state() is None:
        return None
    try:
        with open(RESTORED_MARKER) as f:
            address = f.read().strip()
    except OSError:
        return None
    return address or None


def load_progress():
    try:
        with open(PROGRESS_FILE) as f:
            import json
            return json.load(f)
    except (OSError, ValueError):
        return {}


def save_progress(data):
    import json
    os.makedirs(PROGRESS_DIR, exist_ok=True)
    tmp = PROGRESS_FILE + ".tmp"
    with open(tmp, "w") as f:
        json.dump(data, f)
    os.replace(tmp, PROGRESS_FILE)


def run_helper(args, stdin_text=None):
    return subprocess.run(["sudo", "-n", HELPER] + args,
                          input=stdin_text, capture_output=True,
                          text=True)


def load_site_model():
    path = sitegen.model_path()
    if not os.path.exists(path):
        return None
    try:
        return sitegen.load_model(path)
    except (ValueError, OSError):
        return None


def installed_recipes():
    """The packaged recipes (A23) installed on this machine, as
    their manifests. Recipe packages drop one manifest per
    recipe under /usr/share/onionhost/recipes/; the wizard
    offers exactly what is installed - no recipe is hard-coded
    here, so adding a recipe package adds a wizard choice."""
    found = []
    root = "/usr/share/onionhost/recipes"
    try:
        names = sorted(os.listdir(root))
    except OSError:
        return found
    for name in names:
        try:
            with open(os.path.join(root, name,
                                   "manifest.json")) as f:
                manifest = json.load(f)
        except (OSError, ValueError):
            continue
        if manifest.get("id") == name:
            found.append(manifest)
    return found


UPDATE_STATUS_PATH = "/var/lib/onionhost/update/status.json"
UPDATE_MARKER_PATH = "/var/lib/onionhost/update/fail-closed.marker"


def update_status_text():
    """Dashboard update line (Gate 4): status text only - platform
    updates are automatic (onionhost-update.timer), so there is
    deliberately no button and no new concept. (The one thing that
    IS the owner's - updating their installed app, A26 - is
    reported here as information when a newer packaged version
    exists; the how lives in the Owner Guide, not in a button.)
    The updater records its state as JSON; the fail-closed
    wording matches the state the updater wrote. The updater's
    fail-closed MARKER wins over the status file (Gate 4
    follow-up): a machine that is off for safety must say so even
    if a status write was clobbered or the file is missing - it
    must never be described by a lesser state."""
    import json
    if os.path.exists(UPDATE_MARKER_PATH):
        return ("Your site is off for safety. Updates will install "
                "themselves when a fixed version is ready.")
    try:
        with open(UPDATE_STATUS_PATH) as f:
            record = json.load(f)
        state = record.get("state", "")
    except (OSError, ValueError):
        record, state = {}, ""
    if state in ("up-to-date", "updated"):
        # A26: an installed app with a newer packaged version is
        # a normal, healthy state - the updater reports it as
        # owner_maintained, and the Dashboard words it as plain
        # information (the app is the owner's to update), never
        # as a problem.
        maintained = record.get("owner_maintained") or []
        if maintained:
            app = maintained[0].get("app") or "your app"
            return ("Your software is up to date. A newer %s is "
                    "packaged, but your installed copy is yours "
                    "to update - Manioc Server never changes an "
                    "installed program." % app)
        return "Your software is up to date."
    if state == "fail-closed":
        return ("Your site is off for safety. Updates will install "
                "themselves when a fixed version is ready.")
    return "Updates will install themselves."


RUNTIME_STATUS_PATH = "/var/lib/onionhost/runtime/status.json"
RUNTIME_MARKER_PATH = "/var/lib/onionhost/runtime/fail-closed.marker"


def runtime_status_text():
    """Dashboard runtime line (Repo Review 2 task 20): status text
    only, like the update line - there is nothing for the owner to
    do, so there is deliberately no button. The runtime gate
    (onionhost-runtime-gate-check) records its state as JSON; if it
    found a container running without its protective sandbox
    (gVisor via runsc-wrap) it stopped that part and left the
    fail-closed MARKER, which wins over the status file exactly as
    the updater's marker does: a machine that is off for safety
    must say so even if a status write was clobbered or the file is
    missing. An empty string means all is well - no card."""
    import json
    if os.path.exists(RUNTIME_MARKER_PATH):
        return ("Your site is off for safety. A part of it was not "
                "running inside its protective sandbox, so it was "
                "stopped.")
    try:
        with open(RUNTIME_STATUS_PATH) as f:
            state = json.load(f).get("state", "")
    except (OSError, ValueError):
        state = ""
    if state == "runtime-violation":
        return ("Your site is off for safety. A part of it was not "
                "running inside its protective sandbox, so it was "
                "stopped.")
    return ""


import tkinter as tk  # noqa: E402
from tkinter import filedialog  # noqa: E402


# ------------------------------------------------------------------
# Conventional editing keys (slice 5A)
#
# Tk's class bindings are emacs-flavoured: Ctrl+A moves to the
# start of the line instead of selecting all, and the multi-line
# Text widget swallows Tab as a literal character (which then lands
# in the published text). Owners expect the conventional meanings,
# so every editor field gets explicit bindings that run before the
# class bindings and break the event chain.
# ------------------------------------------------------------------

def _sel_range(widget):
    """(first, last) of the current selection, or None."""
    if isinstance(widget, tk.Text):
        ranges = widget.tag_ranges("sel")
        if not ranges:
            return None
        return str(ranges[0]), str(ranges[1])
    try:
        if not widget.select_present():
            return None
    except tk.TclError:
        return None
    return "sel.first", "sel.last"


def _sel_text(widget):
    sel = _sel_range(widget)
    if sel is None:
        return None
    if isinstance(widget, tk.Text):
        return widget.get(sel[0], sel[1])
    full = widget.get()
    return full[widget.index(sel[0]):widget.index(sel[1])]


def _delete_sel(widget):
    sel = _sel_range(widget)
    if sel is None:
        return False
    if isinstance(widget, tk.Text):
        widget.delete(sel[0], sel[1])
    else:
        widget.delete(widget.index(sel[0]), widget.index(sel[1]))
    return True


def _kb_select_all(widget):
    if isinstance(widget, tk.Text):
        widget.tag_add("sel", "1.0", "end-1c")
        widget.mark_set("insert", "end-1c")
        widget.see("insert")
    else:
        widget.select_range(0, "end")
        widget.icursor("end")
    return "break"


def _kb_copy(widget, cut=False):
    text = _sel_text(widget)
    if text is not None:
        widget.clipboard_clear()
        widget.clipboard_append(text)
        if cut:
            _delete_sel(widget)
    return "break"


def _kb_paste(widget, multiline=False):
    try:
        text = widget.clipboard_get()
    except tk.TclError:
        return "break"
    if not multiline:
        text = text.replace("\r\n", " ").replace("\n", " ") \
                   .replace("\r", " ")
    _delete_sel(widget)
    widget.insert("insert", text)
    return "break"


def _kb_focus(widget, prev=False):
    nxt = widget.tk_focusPrev() if prev else widget.tk_focusNext()
    if nxt is not None:
        nxt.focus_set()
    return "break"


def bind_editing_keys(widget, multiline=False):
    """Ctrl+A select-all, Ctrl+C/X/V conventional, and (for
    multi-line boxes) Tab / Shift-Tab move focus instead of
    inserting a tab character into the content."""
    widget.bind("<Control-a>", lambda e: _kb_select_all(widget))
    widget.bind("<Control-A>", lambda e: _kb_select_all(widget))
    widget.bind("<Control-c>", lambda e: _kb_copy(widget))
    widget.bind("<Control-C>", lambda e: _kb_copy(widget))
    widget.bind("<Control-x>", lambda e: _kb_copy(widget, cut=True))
    widget.bind("<Control-X>", lambda e: _kb_copy(widget, cut=True))
    widget.bind("<Control-v>",
                lambda e: _kb_paste(widget, multiline))
    widget.bind("<Control-V>",
                lambda e: _kb_paste(widget, multiline))
    if multiline:
        widget.bind("<Tab>", lambda e: _kb_focus(widget))
        widget.bind("<Shift-Tab>", lambda e: _kb_focus(widget, True))
        widget.bind("<ISO_Left_Tab>",
                    lambda e: _kb_focus(widget, True))


# ------------------------------------------------------------------
# Site editor (shared by the S1 wizard and the dashboard)
# ------------------------------------------------------------------

class SiteEditor:
    """Edits the site model in a parent frame.

    on_done: called when the user presses the Done button (the
    editor saves the model first). done_label customises it
    ("Continue" in the wizard, "Back" in the dashboard).
    """

    def __init__(self, parent, on_done=None, done_label="Done"):
        self.parent = parent
        self.on_done = on_done
        self.done_label = done_label
        self.model = load_site_model()
        self.frame = tk.Frame(parent)
        self.frame.pack(fill="both", expand=True)
        self.status = None
        if self.model is None:
            self._label("No site yet.")
        else:
            self.build_main()

    # -- small builders ------------------------------------------
    def _clear(self):
        for child in self.frame.winfo_children():
            child.destroy()

    def _label(self, text, fg=None, font="body", pady=(0, 10)):
        kw = {}
        if fg:
            kw["fg"] = fg
        lab = tk.Label(self.frame, text=text, font=FONTS[font],
                       anchor="w", justify="left", wraplength=820,
                       **kw)
        lab.pack(fill="x", pady=pady)
        return lab

    def _button(self, text, command, width=24):
        b = tk.Button(self.frame, text=text, font=FONTS["btn"],
                      command=command, width=width, pady=6)
        b.pack(pady=5)
        return b

    def _items(self):
        if self.model["tier"] == "pages":
            return self.model["pages"]
        return self.model["entries"]

    # -- main page -------------------------------------------------
    def build_main(self):
        self._clear()
        tier_name = ("Simple Pages" if self.model["tier"] == "pages"
                     else "Journal")
        self._label("Your site (%s)" % tier_name, font="title")
        row = tk.Frame(self.frame)
        row.pack(fill="x", pady=4)
        tk.Label(row, text="Site name:", font=FONTS["body"],
                 width=12, anchor="w").pack(side="left")
        self.title_entry = tk.Entry(row, font=FONTS["body"],
                                    width=40)
        self.title_entry.insert(0, self.model["title"])
        self.title_entry.pack(side="left")
        bind_editing_keys(self.title_entry)
        self._label("Pages:" if self.model["tier"] == "pages"
                    else "Entries:")
        self.listbox = tk.Listbox(self.frame, font=FONTS["body"],
                                  height=6)
        self.listbox.pack(fill="x", pady=4)
        self._refresh_list()
        btn_row = tk.Frame(self.frame)
        btn_row.pack(pady=4)
        add_label = ("Add page" if self.model["tier"] == "pages"
                     else "Add entry")
        for text, cmd in ((add_label, self.add_item),
                          ("Edit", self.edit_selected),
                          ("Delete", self.delete_selected)):
            tk.Button(btn_row, text=text, font=FONTS["btn"],
                      command=cmd, width=12, pady=4).pack(
                          side="left", padx=4)
        self.status = self._label("")
        # Save / Publish / Done share ONE row: the full stack did
        # not fit a 900x640 window (Publish + Continue clipped
        # off-screen at 720p-class resolutions - found in slice-4
        # acceptance driving).
        act_row = tk.Frame(self.frame)
        act_row.pack(pady=4)
        for text, cmd in (("Save", self.do_save),
                          ("Publish", self.do_publish)):
            tk.Button(act_row, text=text, font=FONTS["btn"],
                      command=cmd, width=14, pady=5).pack(
                          side="left", padx=4)
        if self.on_done is not None:
            tk.Button(act_row, text=self.done_label,
                      font=FONTS["btn"], command=self._done,
                      width=14, pady=5).pack(side="left", padx=4)

    def _display_items(self):
        """Items in the order the published site shows them. For a
        Journal that is newest first - the same (date, insertion
        index) descending sort sitegen.render_site uses - so the
        editor list matches the site index (slice 5A). Simple Pages
        keep their model order, which IS their site order."""
        items = self._items()
        if self.model["tier"] != "journal":
            return list(items)
        indexed = list(enumerate(items))
        indexed.sort(key=lambda t: (t[1]["date"], t[0]),
                     reverse=True)
        return [item for _, item in indexed]

    def _refresh_list(self):
        self.listbox.delete(0, "end")
        for item in self._display_items():
            if self.model["tier"] == "journal":
                text = "%s  %s" % (item["date"], item["heading"])
            else:
                text = item["heading"]
            self.listbox.insert("end", text)

    def _selected(self):
        sel = self.listbox.curselection()
        if not sel:
            return None
        return self._display_items()[sel[0]]

    def _capture_title(self):
        # The title entry lives on the main page, which is destroyed
        # when the item editor opens. Capture it into the model on
        # EVERY transition away from the main page - otherwise a
        # title typed but not yet Saved is silently lost (found in
        # slice-4 acceptance driving).
        if hasattr(self, "title_entry"):
            try:
                title = self.title_entry.get().strip()
            except tk.TclError:
                return
            if title:
                self.model["title"] = title

    # -- item editing ----------------------------------------------
    def add_item(self):
        self._capture_title()
        items = self._items()
        if self.model["tier"] == "pages" and \
                len(items) >= sitegen.MAX_PAGES:
            self.status.config(
                text="That is the most pages for a Simple Pages "
                     "site. Delete one first if you need room.")
            return
        if self.model["tier"] == "pages":
            item = {"id": sitegen.next_id(self.model, "p"),
                    "heading": "", "text": "", "photo": None}
        else:
            item = {"id": sitegen.next_id(self.model, "e"),
                    "date": datetime.now().strftime("%Y-%m-%d"),
                    "heading": "", "text": "", "photo": None}
        items.append(item)
        self.build_edit(item, new=True)

    def edit_selected(self):
        self._capture_title()
        item = self._selected()
        if item is None:
            self.status.config(text="Choose one from the list "
                                    "first.")
            return
        self.build_edit(item, new=False)

    def delete_selected(self):
        self._capture_title()
        item = self._selected()
        if item is None:
            self.status.config(text="Choose one from the list "
                                    "first.")
            return
        self._items().remove(item)
        self.do_save()
        self.build_main()

    def build_edit(self, item, new=False):
        self._clear()
        self._label("Edit page" if self.model["tier"] == "pages"
                    else "Edit entry", font="title")
        self.edit_item = item
        self.edit_new = new
        self.pending_photo = item.get("photo")

        def field(label, width=12, hint=None, entry_width=44):
            row = tk.Frame(self.frame)
            row.pack(fill="x", pady=4)
            tk.Label(row, text=label, font=FONTS["body"], width=width,
                     anchor="w").pack(side="left")
            e = tk.Entry(row, font=FONTS["body"], width=entry_width)
            e.pack(side="left")
            if hint:
                # The hint is its own element beside the field: the
                # previous design crammed it into the label itself
                # ("Date (2026-10-12):"), which read as state and
                # could clip at narrow widths (slice 5A).
                tk.Label(row, text=hint, font=("Sans", 11),
                         fg="#555555", anchor="w").pack(
                             side="left", padx=(8, 0))
            bind_editing_keys(e)
            return e

        self.heading_entry = field("Heading:")
        self.heading_entry.insert(0, item["heading"])
        self.date_entry = None
        if self.model["tier"] == "journal":
            # entry_width=14: a date is 10 characters. The shared
            # 44-char default left too little row for the hint, whose
            # tail clipped at the window edge in the first slice-5A
            # battery build (measured at the standard 900 px width).
            self.date_entry = field(
                "Date:", hint="year-month-day, like 2026-10-12",
                entry_width=14)
            self.date_entry.insert(0, item["date"])
        self._label("Text:")
        self.text_box = tk.Text(self.frame, font=FONTS["body"],
                                height=5, width=70, wrap="word")
        self.text_box.pack(fill="x", pady=4)
        self.text_box.insert("1.0", item["text"])
        bind_editing_keys(self.text_box, multiline=True)
        prow = tk.Frame(self.frame)
        prow.pack(fill="x", pady=6)
        self.photo_label = tk.Label(prow, font=FONTS["body"],
                                    anchor="w")
        self.photo_label.pack(side="left")
        self._update_photo_label()
        tk.Button(prow, text="Choose photo...", font=FONTS["btn"],
                  command=self.choose_photo, pady=4).pack(
                      side="left", padx=8)
        tk.Button(prow, text="Remove photo", font=FONTS["btn"],
                  command=self.remove_photo, pady=4).pack(side="left")
        self.edit_status = self._label("")
        self._button("Save this", self.save_item)
        self._button("Cancel", self.build_main, width=16)

    def _update_photo_label(self):
        if self.pending_photo:
            self.photo_label.config(
                text="Photo: %s..." % self.pending_photo[:12])
        else:
            self.photo_label.config(text="No photo")

    def choose_photo(self):
        start = os.path.expanduser("~/Pictures")
        if not os.path.isdir(start):
            start = os.path.expanduser("~")
        path = filedialog.askopenfilename(
            initialdir=start, title="Choose a photo",
            filetypes=[("Photos", "*.jpg *.jpeg *.png *.webp "
                                  "*.gif *.bmp"),
                       ("All files", "*.*")])
        if not path:
            return
        try:
            name = sitegen.ingest_photo(path)
        except Exception as e:  # noqa: BLE001 - show and continue
            self.edit_status.config(
                text="That photo could not be used: %s" % e)
            return
        self.pending_photo = name
        self._update_photo_label()
        self.edit_status.config(
            text="Photo added. Its hidden data (location and times) "
                 "was removed.")

    def remove_photo(self):
        self.pending_photo = None
        self._update_photo_label()

    def save_item(self):
        item = self.edit_item
        heading = self.heading_entry.get().strip()
        if not heading:
            self.edit_status.config(text="Give it a heading first.")
            return
        item["heading"] = heading
        item["text"] = self.text_box.get("1.0", "end-1c")
        item["photo"] = self.pending_photo
        if self.date_entry is not None:
            date = self.date_entry.get().strip()
            try:
                datetime.strptime(date, "%Y-%m-%d")
            except ValueError:
                self.edit_status.config(
                    text="The date must look like 2026-10-12.")
                return
            item["date"] = date
        self.build_main()
        self.do_save()

    # -- save / publish ----------------------------------------------
    def do_save(self):
        if hasattr(self, "title_entry"):
            title = self.title_entry.get().strip()
            if title:
                self.model["title"] = title
        try:
            sitegen.save_model(self.model)
        except (ValueError, OSError) as e:
            if self.status is not None:
                self.status.config(text="Could not save: %s" % e)
            return False
        if self.status is not None:
            self.status.config(text="Saved.")
        return True

    def do_publish(self):
        if not self.do_save():
            return
        if self.status is not None:
            self.status.config(text="Publishing...")
        proc = run_helper(["publish"])
        if proc.returncode == 0:
            msg = "Published. Your site shows the new version now."
        else:
            msg = ("Publishing failed: " +
                   (proc.stderr.strip()[:200] or "unknown error"))
        if self.status is not None:
            self.status.config(text=msg)

    def _done(self):
        self._capture_title()
        self.do_save()
        if self.on_done is not None:
            self.on_done()


# ------------------------------------------------------------------
# First-boot wizard
# ------------------------------------------------------------------

class Wizard:
    def __init__(self, root, kiosk):
        self.root = root
        self.kiosk = kiosk
        self.state = read_state()
        self.progress = load_progress()
        self.phrase = None
        self.check_pos = []
        self.editor = None
        root.title("Manioc Server Setup")
        if kiosk:
            root.attributes("-fullscreen", True)
        else:
            # As tall as the screen allows (up to 760): editor
            # forms must never push buttons off a small screen.
            root.geometry("900x%d" % min(760,
                                          root.winfo_screenheight() - 30))
        self.title_font = FONTS["title"]
        self.body_font = FONTS["body"]
        self.word_font = FONTS["word"]
        self.btn_font = FONTS["btn"]
        self.frame = tk.Frame(root, padx=36, pady=28)
        self.frame.pack(fill="both", expand=True)

    # -- small builders ----------------------------------------------
    def clear(self):
        for child in self.frame.winfo_children():
            child.destroy()
        self.editor = None

    def title(self, text):
        tk.Label(self.frame, text=text, font=self.title_font,
                 anchor="w").pack(fill="x", pady=(0, 14))

    def body(self, text):
        tk.Label(self.frame, text=text, font=self.body_font,
                 anchor="w", justify="left",
                 wraplength=820).pack(fill="x", pady=(0, 12))

    def button(self, text, command, width=28):
        b = tk.Button(self.frame, text=text, font=self.btn_font,
                      command=command, width=width, pady=8)
        b.pack(pady=10)
        return b

    # -- S0 ------------------------------------------------------------
    def page_s0_welcome(self):
        self.clear()
        self.title("Welcome to your Manioc Server")
        self.body("Let's finish setting up. First, this computer "
                  "will make up a short login phrase for you - "
                  "3 words. You will use it to log in to this "
                  "computer's screen (it is different from the disk "
                  "passphrase you wrote down during installation).")
        self.body("Get a pen and the same piece of paper, or a new "
                  "one, ready.")
        self.button("Make my login phrase", self.page_s0_phrase)

    def page_s0_phrase(self):
        self.clear()
        # Generate ONCE per wizard session: "Show the words again"
        # must show the SAME words the user already copied, never a
        # fresh phrase (a regenerate-on-show bug here made
        # verification unpassable against the first paper copy -
        # found in slice-2 testing).
        if self.phrase is None:
            self.phrase = phrasegen.generate(3)
        words = self.phrase.split(" ")
        self.title("Your login phrase")
        self.body("Write these 3 words on paper, in order:")
        tk.Label(self.frame, text="   ".join(
            "%d. %s" % (i + 1, w) for i, w in enumerate(words)),
            font=self.word_font, anchor="w").pack(fill="x", pady=16)
        self.body("You will type this phrase at the login screen "
                  "every time. If you lose it, someone with the disk "
                  "passphrase paper can reset it from Maintenance.")
        self.button("I have written them down", self.page_s0_verify)

    def page_s0_verify(self):
        self.clear()
        words = self.phrase.split(" ")
        self.check_pos = sorted(random.sample([1, 2, 3], 2))
        self.title("Check your paper")
        self.body("Type these words from your paper:")
        self.entries = []
        for pos in self.check_pos:
            row = tk.Frame(self.frame)
            row.pack(fill="x", pady=6)
            tk.Label(row, text="Word number %d:" % pos,
                     font=self.body_font, width=18,
                     anchor="w").pack(side="left")
            e = tk.Entry(row, font=("Monospace", 16), width=22)
            e.pack(side="left")
            bind_editing_keys(e)
            self.entries.append((pos, e))
        self.verify_error = tk.Label(self.frame, text="",
                                     font=self.body_font, fg="#b00020",
                                     anchor="w")
        self.verify_error.pack(fill="x", pady=6)
        self.button("Set my login phrase", self.do_commit_login)
        self.button("Show the words again", self.page_s0_phrase,
                    width=22)

    def do_commit_login(self):
        words = self.phrase.split(" ")
        for pos, entry in self.entries:
            if entry.get().strip().lower() != words[pos - 1].lower():
                self.verify_error.config(
                    text="Word number %d does not match. Check your "
                         "paper and try again." % pos)
                return
        proc = run_helper(["commit-login"],
                          stdin_text=self.phrase + "\n")
        if proc.returncode != 0:
            self.verify_error.config(
                text="Something went wrong setting the login phrase: "
                     + (proc.stderr.strip()[:200] or "unknown error"))
            return
        self.clear()
        self.title("Login phrase set")
        self.body("The computer will now restart to the login "
                  "screen. Log in with your 3-word login phrase to "
                  "continue setup.")
        # LightDM restarts ~2 s after the helper exits; keep the
        # message up until the session ends.

    # -- S1 ------------------------------------------------------------
    def page_s1_sitetype(self):
        self.clear()
        self.title("What kind of website?")
        self.body("Choose what your site will be. Simple Pages is "
                  "a few pages about anything. Journal is dated "
                  "posts, newest first. Your own application is a "
                  "program you install yourself, like a forum - "
                  "that one is for people comfortable installing "
                  "software. You can switch later, but switching "
                  "starts a fresh site.")
        existing = load_site_model()
        default = (existing or {}).get(
            "tier", self.progress.get("siteType", "pages"))
        self.site_var = tk.StringVar(value=default)
        for value, label in (("pages", "Simple Pages - a few pages "
                                       "about you or your project"),
                             ("journal", "Journal - dated posts, "
                                         "newest first"),
                             ("app", "Your own application - a "
                                     "forum or other program you "
                                     "install yourself")):
            tk.Radiobutton(self.frame, text=label, value=value,
                           variable=self.site_var,
                           font=self.body_font, anchor="w",
                           justify="left").pack(fill="x", pady=4)

        def next_page():
            tier = self.site_var.get()
            self.progress["siteType"] = tier
            model = load_site_model()
            if model is None or model["tier"] != tier:
                sitegen.save_model(sitegen.starter_model(tier))
            if tier == "app":
                self.progress["step"] = "appinfo"
                save_progress(self.progress)
                self.page_s1_appinfo()
                return
            self.progress["step"] = "editor"
            save_progress(self.progress)
            self.page_s1_editor()
        self.button("Continue", next_page)

    def page_s1_appinfo(self):
        """The app kind has no editor: the application IS the
        site. This page is the whole brief in plain words - the
        full contract is in the project's APP-SITES.md - plus the
        one choice the platform needs: which runtime the slot
        provides."""
        self.clear()
        self.title("Your own application")
        self.body("Manioc Server will run a program that you install "
                  "into a folder on this computer, and serve it at "
                  "your .onion address. The program runs in the "
                  "same sealed room as every Manioc Server site: it "
                  "has no network of its own, so even a hacked "
                  "program cannot find or reveal this computer's "
                  "address.")
        self.body("Two honest limits: the program cannot send "
                  "email (there is no way out), and whatever the "
                  "program stores - forum posts, member accounts - "
                  "lives on this computer and is only as safe as "
                  "the program itself. Your address stays hidden "
                  "either way.")
        # A23: a packaged recipe is the no-work START - the
        # platform installs the app once; updating it afterwards
        # is the owner's (A26), stated plainly below at the
        # moment of choosing. The owner chooses the
        # administrator's name and password, which the recipe's
        # seeding needs (never invented, never stored in the
        # site model: held in this window's memory until Go Live
        # stages them through the helper). The choices offered
        # are the recipe packages installed on this machine -
        # nothing is hard-coded per recipe.
        self.body("Manioc Server can set one of these up for you - "
                  "it installs the software once, and after that "
                  "updating it is up to you, the way it is with "
                  "any program you own - or you can install your "
                  "own program:")
        model = load_site_model() or {}
        self.recipe_manifests = {m["id"]: m
                                 for m in installed_recipes()}
        chosen = model.get("recipe")
        self.recipe_var = tk.StringVar(
            value=chosen if chosen in self.recipe_manifests
            else "own")

        def recipe_toggle():
            # Late-bound closure: the widgets it touches are all
            # created below; it runs on clicks and once at the end
            # of this page's construction.
            manifest = self.recipe_manifests.get(
                self.recipe_var.get())
            if manifest is not None:
                self.recipe_fields.pack(fill="x", pady=6,
                                        before=self.runtime_label)
                for btn in self.runtime_buttons:
                    btn.config(state="disabled")
                runtime = {"php": "PHP"}.get(
                    manifest.get("runtime"),
                    manifest.get("runtime", ""))
                self.runtime_label.config(
                    text="%s runs on the %s runtime - no choice "
                         "needed." % (manifest["name"], runtime))
                self.recipe_note.config(
                    text=manifest.get("admin_note", ""))
            else:
                self.recipe_fields.pack_forget()
                for btn in self.runtime_buttons:
                    btn.config(state="normal")
                self.runtime_label.config(
                    text="Which kind of program will you install?")
        choices = [(m["id"], m["description"])
                   for m in self.recipe_manifests.values()]
        choices.append(("own", "My own program - I will install "
                               "it myself"))
        for value, label in choices:
            tk.Radiobutton(self.frame, text=label, value=value,
                           variable=self.recipe_var,
                           command=recipe_toggle,
                           font=self.body_font, anchor="w",
                           justify="left",
                           wraplength=820).pack(fill="x", pady=4)
        self.recipe_fields = tk.Frame(self.frame)
        tk.Label(self.recipe_fields, text="Administrator name:",
                 font=self.body_font, anchor="w").pack(fill="x")
        self.admin_user_entry = tk.Entry(
            self.recipe_fields, font=self.body_font)
        self.admin_user_entry.pack(fill="x", pady=2)
        tk.Label(self.recipe_fields, text="Administrator "
                 "password (at least 8 characters):",
                 font=self.body_font, anchor="w").pack(fill="x")
        self.admin_pass_entry = tk.Entry(
            self.recipe_fields, font=self.body_font, show="*")
        self.admin_pass_entry.pack(fill="x", pady=2)
        tk.Label(self.recipe_fields, text="Type the password "
                 "again:", font=self.body_font,
                 anchor="w").pack(fill="x")
        self.admin_pass2_entry = tk.Entry(
            self.recipe_fields, font=self.body_font, show="*")
        self.admin_pass2_entry.pack(fill="x", pady=2)
        self.recipe_note = tk.Label(
            self.recipe_fields, text="",
            font=self.body_font, anchor="w",
            justify="left", wraplength=820)
        self.recipe_note.pack(fill="x", pady=4)
        self.recipe_error = tk.Label(self.frame, text="",
                                     font=self.body_font,
                                     fg="#b00020", anchor="w")
        self.recipe_error.pack(fill="x", pady=4)

        self.runtime_label = tk.Label(
            self.frame, text="Which kind of program will you "
            "install?", font=self.body_font, anchor="w")
        self.runtime_label.pack(fill="x", pady=(8, 0))
        self.runtime_var = tk.StringVar(
            value=model.get("runtime", "php"))
        self.runtime_buttons = []
        for value, label in (
                ("php", "A PHP program (a forum like SMF, "
                        "WordPress, most web software) - comes "
                        "with a database"),
                ("native", "A single program file I supply "
                           "(for example a Rust program) - it "
                           "brings its own storage")):
            btn = tk.Radiobutton(self.frame, text=label,
                                 value=value,
                                 variable=self.runtime_var,
                                 font=self.body_font, anchor="w",
                                 justify="left", wraplength=820)
            btn.pack(fill="x", pady=4)
            self.runtime_buttons.append(btn)

        recipe_toggle()

        def next_page():
            model = load_site_model()
            if model is None or model["tier"] != "app":
                model = sitegen.starter_model("app")
            manifest = self.recipe_manifests.get(
                self.recipe_var.get())
            if manifest is not None:
                user = self.admin_user_entry.get().strip()
                pw = self.admin_pass_entry.get()
                pw2 = self.admin_pass2_entry.get()
                if not user:
                    self.recipe_error.config(
                        text="Choose a name for the "
                             "administrator.")
                    return
                if len(pw) < 8:
                    self.recipe_error.config(
                        text="The administrator password needs "
                             "at least 8 characters.")
                    return
                if pw != pw2:
                    self.recipe_error.config(
                        text="The two passwords do not match.")
                    return
                model["recipe"] = manifest["id"]
                model["runtime"] = manifest["runtime"]
                # Memory only - staged via the helper at Go Live,
                # consumed and shredded by the recipe machinery.
                self.recipe_admin = (user, pw)
            else:
                model.pop("recipe", None)
                model["runtime"] = self.runtime_var.get()
                self.recipe_admin = None
            sitegen.save_model(model)
            self.progress["step"] = "golive"
            save_progress(self.progress)
            self.page_s1_golive()
        self.button("Continue", next_page)

    def page_s1_editor(self):
        self.clear()
        self.title("Write your site")
        self.body("Here is your starter site. Change anything you "
                  "like, then press Continue. You can edit it again "
                  "any time after setup.")
        holder = tk.Frame(self.frame)
        holder.pack(fill="both", expand=True)
        self.editor = SiteEditor(
            holder, on_done=self._editor_done, done_label="Continue")

    def _editor_done(self):
        self.progress["step"] = "golive"
        save_progress(self.progress)
        self.page_s1_golive()

    def page_s1_golive(self):
        self.clear()
        self.title("Go live")
        self.body("Your website software is already running. "
                  "Pressing Go Live publishes your site at your "
                  ".onion address and finishes setup.")
        # The safety warning the public explainer and the Owner
        # Guide have always said this page carries - it did not
        # exist until the deanonymization audit (R-09) found the
        # claim shipped without the warning. This is the step
        # where the owner commits to going live, so this is where
        # it belongs, before the button.
        self.body("One honest warning before you go live. This "
                  "system hides your computer's network address - "
                  "it cannot hide when the computer is online. If "
                  "being physically located would put you in "
                  "danger, do not rely on hosting from your home.")
        self.body("After this, use the Manioc Server app on the "
                  "desktop to edit your site and check it is up.")
        self.golive_error = tk.Label(self.frame, text="",
                                     font=self.body_font, fg="#b00020",
                                     anchor="w")
        self.golive_error.pack(fill="x", pady=6)

        def go_live():
            # A23 recipe sites: stage the administrator details
            # the app page collected (held in memory only) through
            # the helper, root-only, just before publish - the
            # recipe machinery consumes and shreds them while
            # seeding. The site title rides along as a fourth
            # line for recipes whose installer asks for one. If
            # the wizard was restarted after the app page (power
            # cut, reboot), the details are gone: go back and
            # collect them again rather than inventing any.
            model = load_site_model() or {}
            if model.get("recipe"):
                staged = getattr(self, "recipe_admin", None)
                if not staged:
                    self.progress["step"] = "appinfo"
                    save_progress(self.progress)
                    self.page_s1_appinfo()
                    return
                proc = run_helper(
                    ["recipe-setup"],
                    stdin_text="%s\n%s\n%s\n%s"
                               % (model["recipe"], staged[0],
                                  staged[1],
                                  model.get("title", "")))
                if proc.returncode != 0:
                    self.golive_error.config(
                        text="Could not save the administrator "
                             "details: "
                             + (proc.stderr.strip()[:200] or "?"))
                    return
            proc = run_helper(["publish"])
            if proc.returncode != 0:
                self.golive_error.config(
                    text="Publishing failed: "
                         + (proc.stderr.strip()[:200] or "?"))
                return
            proc = run_helper(["set-state", "S2"])
            if proc.returncode != 0:
                self.golive_error.config(
                    text="Could not finish setup: "
                         + (proc.stderr.strip()[:200] or "?"))
                return
            self.progress["step"] = "done"
            save_progress(self.progress)
            self.clear()
            self.title("You are live")
            self.body("Setup is complete. Your site is on the "
                      "Tor network.")
            self.button("Close", self.root.destroy)
        self.button("Go Live", go_live)

    def page_s1_restored(self):
        """Shown when a backup was restored from Maintenance before
        setup finished: the site and its address are already back;
        the only step left is finishing setup (S1 -> S2)."""
        self.clear()
        self.title("Your website is back")
        onion = read_restored_onion() or ""
        self.body("You restored a backup onto this computer. Your "
                  "website and its address came back with it:")
        tk.Label(self.frame, text=onion, font=("Monospace", 15),
                 anchor="w", wraplength=820, justify="left").pack(
                     fill="x", pady=(0, 12))
        self.body("Nothing else to set up - press the button and "
                  "you are done. Your pages, your journal and your "
                  "photos are the ones from the backup.")
        self.restored_error = tk.Label(self.frame, text="",
                                       font=self.body_font,
                                       fg="#b00020", anchor="w")
        self.restored_error.pack(fill="x", pady=6)

        def finish():
            proc = run_helper(["set-state", "S2"])
            if proc.returncode != 0:
                self.restored_error.config(
                    text="Could not finish setup: "
                         + (proc.stderr.strip()[:200] or "?"))
                return
            self.progress["step"] = "done"
            save_progress(self.progress)
            self.clear()
            self.title("You are live")
            self.body("Setup is complete. Your restored site is "
                      "on the Tor network at its usual address.")
            self.button("Close", self.root.destroy)
        self.button("Finish setup", finish)

    # -- entry ---------------------------------------------------------
    def run(self):
        if self.state == "S0":
            self.page_s0_welcome()
        elif self.state == "S1":
            if read_restored_onion() and load_site_model() is not None:
                self.page_s1_restored()
                return
            step = self.progress.get("step")
            model = load_site_model()
            if step == "golive":
                self.page_s1_golive()
            elif step == "appinfo" or \
                    (model is not None and model["tier"] == "app"
                     and step != "golive"):
                if model is None:
                    self.page_s1_sitetype()
                else:
                    self.page_s1_appinfo()
            elif step == "editor":
                if model is None:
                    self.page_s1_sitetype()
                else:
                    self.page_s1_editor()
            else:
                self.page_s1_sitetype()
        else:
            self.root.destroy()


# ------------------------------------------------------------------
# Dashboard (state S2): site summary + status card + Edit
# ------------------------------------------------------------------

class Dashboard:
    def __init__(self, root):
        self.root = root
        root.title("Manioc Server")
        root.geometry("900x%d" % min(760,
                                      root.winfo_screenheight() - 30))
        self.frame = tk.Frame(root, padx=36, pady=28)
        self.frame.pack(fill="both", expand=True)
        self.editor = None
        self.build_main()

    def clear(self):
        for child in self.frame.winfo_children():
            child.destroy()
        self.editor = None

    def build_main(self):
        self.clear()
        tk.Label(self.frame, text="Your website",
                 font=FONTS["title"], anchor="w").pack(
                     fill="x", pady=(0, 14))
        model = load_site_model()
        if model is None:
            text = "No site yet."
            tier = ""
            is_app = False
        else:
            text = model["title"]
            is_app = model["tier"] == "app"
            tier = ("Simple Pages" if model["tier"] == "pages"
                    else "Journal" if model["tier"] == "journal"
                    else "Your own application")
        tk.Label(self.frame, text=text, font=FONTS["body"],
                 anchor="w").pack(fill="x", pady=2)
        if tier:
            tk.Label(self.frame, text=tier, font=FONTS["body"],
                     anchor="w").pack(fill="x", pady=2)
        self.status_label = tk.Label(
            self.frame, text="Checking your site...", font=FONTS["body"],
            anchor="w", justify="left", wraplength=820)
        self.status_label.pack(fill="x", pady=14)
        # Gate 4: the update line - status text only, no button,
        # no new concept (updates install themselves; see
        # update_status_text). Refreshed with every status check.
        self.update_label = tk.Label(
            self.frame, text=update_status_text(), font=FONTS["body"],
            anchor="w", justify="left", wraplength=820)
        self.update_label.pack(fill="x", pady=(0, 10))
        # Repo Review 2 task 20: the runtime-gate line - status
        # text only, no button (see runtime_status_text). Empty
        # when every container is in its sandbox. Refreshed with
        # every status check.
        self.runtime_label = tk.Label(
            self.frame, text=runtime_status_text(), font=FONTS["body"],
            anchor="w", justify="left", wraplength=820)
        self.runtime_label.pack(fill="x", pady=(0, 10))
        tk.Button(self.frame,
                  text="Application details" if is_app
                  else "Edit site",
                  font=FONTS["btn"],
                  command=self.open_editor, width=24, pady=8).pack(
                      pady=8)
        tk.Button(self.frame, text="Back up", font=FONTS["btn"],
                  command=self.build_backup, width=24, pady=8).pack(
                      pady=4)
        tk.Button(self.frame, text="Check again", font=FONTS["btn"],
                  command=self.check_status, width=24, pady=8).pack(
                      pady=4)
        # Every (re)build of the main page starts a fresh probe:
        # returning from the editor (Back, possibly after Publish)
        # must not leave the card sitting on "Checking your site..."
        # with nobody coming back to fill it in (slice 5A).
        self.check_status()

    def open_editor(self):
        model = load_site_model()
        if model is not None and model["tier"] == "app":
            self.build_app_page()
            return
        self.clear()
        holder = tk.Frame(self.frame)
        holder.pack(fill="both", expand=True)
        self.editor = SiteEditor(holder, on_done=self.build_main,
                                 done_label="Back")

    # -- app details (slice 6B) ------------------------------------
    def build_app_page(self):
        """For an app site there is no platform editor - the
        application is the site. This page carries the slot's
        facts the owner needs to install and configure their
        program: where the folder is, and the database details
        (fetched through the helper; the stored record itself is
        readable only by root and the app container)."""
        self.clear()
        tk.Label(self.frame, text="Your application",
                 font=FONTS["title"], anchor="w").pack(
                     fill="x", pady=(0, 14))

        def body(text):
            tk.Label(self.frame, text=text, font=FONTS["body"],
                     anchor="w", justify="left",
                     wraplength=820).pack(fill="x", pady=(0, 12))
        model = load_site_model() or {}
        runtime = model.get("runtime", "php")
        if runtime == "native":
            body("Your site is a program you supplied. Put the "
                 "program file in the program folder below and "
                 "name it \"app\". It is run with its folder as "
                 "its working folder, and it must listen on the "
                 "unix socket named by the ONIONHOST_APP_SOCKET "
                 "environment variable. Its data stays in its "
                 "folder.")
            folder = "/var/lib/onionhost/appdata/native"
        else:
            body("Your site is a PHP application you installed in "
                 "the app folder below. Manioc Server serves its files "
                 "and gives it a database:")
            folder = "/var/lib/onionhost/appdata/www"
        self.app_info_label = tk.Label(
            self.frame, text="Reading the details...",
            font=FONTS["body"], anchor="w", justify="left",
            wraplength=820)
        self.app_info_label.pack(fill="x", pady=6)

        def work():
            proc = run_helper(["app-info"])
            info = {}
            for line in proc.stdout.splitlines():
                if "=" in line:
                    key, _, value = line.partition("=")
                    info[key] = value
            lines = ["App folder: %s" % folder]
            if runtime != "native" and info.get("DB_NAME"):
                lines += [
                    "Database name: %s" % info["DB_NAME"],
                    "Database user: %s" % info.get("DB_USER", ""),
                    "Database password: %s"
                    % info.get("DB_PASSWORD", ""),
                    "Database host: localhost (its socket is "
                    "already the PHP default; socket path inside "
                    "the app: /run/mysqld/mysqld.sock)",
                ]
            text = "\n".join(lines)

            def apply():
                try:
                    self.app_info_label.config(text=text)
                except tk.TclError:
                    pass
            self.root.after(0, apply)
        threading.Thread(target=work, daemon=True).start()
        body("Remember: the application cannot send email, and "
             "it can only be reached at your .onion address - "
             "which is the point.")
        tk.Button(self.frame, text="Open the folder",
                  font=FONTS["btn"],
                  command=lambda: subprocess.Popen(
                      ["xdg-open", folder]),
                  width=24, pady=8).pack(pady=8)
        tk.Button(self.frame, text="Back", font=FONTS["btn"],
                  command=self.build_main, width=24, pady=8).pack(
                      pady=4)

    # -- backup (slice 5B, DESIGN-v3 A3) ------------------------------
    def build_backup(self):
        self.clear()
        tk.Label(self.frame, text="Back up your website",
                 font=FONTS["title"], anchor="w").pack(
                     fill="x", pady=(0, 14))

        def body(text):
            tk.Label(self.frame, text=text, font=FONTS["body"],
                     anchor="w", justify="left",
                     wraplength=820).pack(fill="x", pady=(0, 12))
        body("A backup is one file that holds your whole website: "
             "your pages, your journal, your photos - and the "
             "secret that gives your site its address. With this "
             "file and the disk passphrase from your paper, you can "
             "bring your website back on a new computer, with the "
             "same address.")
        _model = load_site_model()
        if _model is not None and _model["tier"] == "app":
            body("For an application site, the backup also holds "
                 "the application's own files and a copy of its "
                 "database, so the restored site comes back with "
                 "its posts and members as they were.")
        body("No passphrase is needed to make a backup. The file is "
             "locked so that only your disk passphrase can open "
             "it, later, when you restore.")
        body("This backup IS your website. Guard it like the "
             "Recovery Sheet. Don't keep the backup stick in the "
             "same drawer as the paper.")
        self.backup_status = tk.Label(
            self.frame, text="", font=FONTS["body"], anchor="w",
            justify="left", wraplength=820)
        self.backup_status.pack(fill="x", pady=10)
        tk.Button(self.frame, text="Choose where to save...",
                  font=FONTS["btn"], command=self.do_backup,
                  width=24, pady=8).pack(pady=8)
        tk.Button(self.frame, text="Back", font=FONTS["btn"],
                  command=self.build_main, width=24, pady=8).pack(
                      pady=4)

    def do_backup(self):
        dest = filedialog.asksaveasfilename(
            title="Save your website backup",
            defaultextension=".onionhost-backup",
            filetypes=[("OnionHost backup", "*.onionhost-backup")],
            initialfile="my-website-backup.onionhost-backup")
        if not dest:
            return
        self.backup_status.config(text="Making your backup...")
        label = self.backup_status

        def work():
            proc = run_helper(["backup", dest])
            if proc.returncode == 0:
                text = ("Backup saved:\n%s\n\nKeep it safe. Together "
                        "with the disk passphrase on your paper, "
                        "this file can bring your whole website "
                        "back." % dest)
            else:
                text = ("The backup could not be made:\n"
                        + (proc.stderr.strip()[:240]
                           or "unknown error"))

            def apply():
                try:
                    label.config(text=text)
                except tk.TclError:
                    pass  # page navigated away meanwhile
            self.root.after(0, apply)
        threading.Thread(target=work, daemon=True).start()

    def check_status(self):
        if not hasattr(self, "status_label"):
            return
        # Generation guard: probes are slow (Tor), and a rebuild of
        # this page (e.g. returning from the editor) starts a new
        # one - a late result from an older probe must never
        # overwrite a newer check's outcome.
        self._probe_gen = getattr(self, "_probe_gen", 0) + 1
        gen = self._probe_gen
        self.status_label.config(text="Checking your site...")

        def work():
            proc = run_helper(["probe-status"])
            # PROBE_OK means "an HTTP response came back through the
            # onion path"; require a 200 as well - a site answering
            # 403/404 is reachable but not "up" (slice-4 finding).
            ok = proc.returncode == 0 and "PROBE_OK" in proc.stdout \
                and " 200 " in proc.stdout
            if ok:
                text = "Your site is up and reachable."
            else:
                text = ("Your site is not reachable yet. Give it a "
                        "few minutes after starting the computer, "
                        "then check again.")

            def apply():
                if gen != self._probe_gen:
                    return
                try:
                    self.status_label.config(text=text)
                    self.update_label.config(
                        text=update_status_text())
                    self.runtime_label.config(
                        text=runtime_status_text())
                except tk.TclError:
                    pass  # the page was rebuilt again meanwhile
            self.root.after(0, apply)
        threading.Thread(target=work, daemon=True).start()


def main():
    if "--dashboard" in sys.argv:
        if read_state() != "S2":
            return 0  # the dashboard exists only after setup
        root = tk.Tk()
        Dashboard(root)
        root.mainloop()
        return 0
    kiosk = "--kiosk" in sys.argv
    state = read_state()
    if state not in ("S0", "S1"):
        return 0  # S2 / unknown: never show the setup wizard.
    root = tk.Tk()
    Wizard(root, kiosk).run()
    root.mainloop()
    return 0


if __name__ == "__main__":
    sys.exit(main())
