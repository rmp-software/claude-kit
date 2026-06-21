#!/usr/bin/env python3
"""Shared stack detection for the tailwind-standard plugin hooks.

Dependency-free, side-effect-free, never raises. Both hooks import it via:

    import os, sys
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    from _detect import detect_stack

`detect_stack(cwd)` returns the two signals INDEPENDENTLY as a tuple
`(tailwind_v4, shadcn)`. Tailwind v4 is the hard requirement; shadcn is an
OPTIONAL layer that can only exist where Tailwind already does. On any error or
ambiguity it returns `(False, False)` rather than guessing.

Detection is cheap and bounded: it reads a handful of files, caps the directory
scan depth, skips heavy dirs, and (in a monorepo) also scans the repo root so an
app-dir caller still sees a shared-UI package's shadcn signal.
"""

import os
import re

# --- Bounded-scan limits (keep detection cheap; never walk a whole tree) ------
MAX_DEPTH = 2            # directory levels below cwd to descend
MAX_FILES_READ = 40      # hard cap on files we open during detection
MAX_READ_BYTES = 65536   # bytes read per file when sniffing content
SKIP_DIRS = {
    "node_modules", ".git", ".next", "dist", "build", "out",
    ".turbo", "coverage", ".vercel", ".cache", "vendor",
}

# Tailwind v4: a major-4+ tailwindcss dep, or the v4 postcss plugin.
TAILWIND_DEP_RE = re.compile(r'"tailwindcss"\s*:\s*"([^"]+)"')
TAILWIND_POSTCSS_RE = re.compile(r'"@tailwindcss/postcss"\s*:\s*"')
TAILWIND_V4_IMPORT_RE = re.compile(r"""@import\s+["']tailwindcss["']""")

# shadcn: a cva / tailwind-merge dep, or a cn() merge util.
SHADCN_DEP_RE = re.compile(r'"(class-variance-authority|tailwind-merge)"\s*:\s*"')
CN_UTIL_RE = re.compile(r"clsx\([^)]*\)|twMerge\(|tailwind-merge")


def iter_files(root):
    """Yield bounded (path) tuples up to MAX_DEPTH / MAX_FILES_READ. Never raises."""
    count = 0
    root = os.path.abspath(root)
    for dirpath, dirnames, filenames in os.walk(root):
        # Depth gate, relative to root.
        rel = os.path.relpath(dirpath, root)
        depth = 0 if rel == "." else rel.count(os.sep) + 1
        if depth > MAX_DEPTH:
            dirnames[:] = []
            continue
        dirnames[:] = [
            d for d in dirnames
            if d not in SKIP_DIRS and not d.startswith(".")
        ]
        for name in filenames:
            yield os.path.join(dirpath, name)
            count += 1
            if count >= MAX_FILES_READ:
                return


def read_head(path):
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as fh:
            return fh.read(MAX_READ_BYTES)
    except Exception:
        return ""


def tailwind_v4_pkg(text):
    """True if a package.json body declares Tailwind v4 (dep major >= 4, or v4 postcss)."""
    if TAILWIND_POSTCSS_RE.search(text):
        return True
    m = TAILWIND_DEP_RE.search(text)
    if not m:
        return False
    ver = m.group(1)
    # Strip leading range chars, grab the first numeric component.
    digits = re.search(r"(\d+)", ver)
    if not digits:
        # A non-numeric spec ("latest", "workspace:*") is ambiguous — don't claim v4.
        return False
    try:
        return int(digits.group(1)) >= 4
    except Exception:
        return False


MONOREPO_MARKERS = ("pnpm-workspace.yaml", "lerna.json", "turbo.json")


def monorepo_root(cwd):
    """Walk up from cwd for a monorepo root marker. None if cwd isn't in one.

    A shared-UI package (where shadcn primitives + cva/tailwind-merge live) is
    usually a sibling of the app under `packages/*`, so an app-dir session needs
    the root included in the scan to see the shadcn signal. Bounded walk-up,
    never raises.
    """
    try:
        d = os.path.abspath(cwd)
        while True:
            for marker in MONOREPO_MARKERS:
                if os.path.exists(os.path.join(d, marker)):
                    return d
            # Root package.json declaring workspaces also marks a monorepo.
            pkg = os.path.join(d, "package.json")
            if os.path.exists(pkg) and '"workspaces"' in read_head(pkg):
                return d
            parent = os.path.dirname(d)
            if parent == d:
                return None
            d = parent
    except Exception:
        return None


def scan_roots(cwd):
    """The bounded set of roots to scan: cwd, plus the monorepo root if distinct."""
    roots = [os.path.abspath(cwd)]
    root = monorepo_root(cwd)
    if root and os.path.abspath(root) != roots[0]:
        roots.append(os.path.abspath(root))
    return roots


def detect_stack(cwd):
    """Best-effort: return the two signals INDEPENDENTLY as (tailwind_v4, shadcn).

    Tailwind v4 is the hard requirement; shadcn is an optional layer (it can only
    exist where Tailwind already does, but the reverse is not true — a repo may use
    Tailwind v4 + tokens WITHOUT shadcn). The signals are computed separately so a
    caller can gate on Tailwind alone and treat shadcn as conditional.

    Scans the cwd and (when in a monorepo) the repo root, so an app-dir caller
    still sees a shared-UI package's shadcn signal. Bounded, side-effect-free,
    and returns (False, False) on any error.
    """
    try:
        tailwind = False
        shadcn = False
        for root in scan_roots(cwd):
            for path in iter_files(root):
                base = os.path.basename(path)

                if base == "package.json":
                    text = read_head(path)
                    if not tailwind and tailwind_v4_pkg(text):
                        tailwind = True
                    if not shadcn and SHADCN_DEP_RE.search(text):
                        shadcn = True

                elif base == "components.json":
                    # shadcn's registry/config file — a strong shadcn signal.
                    shadcn = True

                elif base.endswith(".css"):
                    if not tailwind:
                        text = read_head(path)
                        if TAILWIND_V4_IMPORT_RE.search(text):
                            tailwind = True

                elif base in ("utils.ts", "cn.ts", "cn.tsx", "utils.tsx"):
                    if not shadcn:
                        text = read_head(path)
                        if CN_UTIL_RE.search(text):
                            shadcn = True

                if tailwind and shadcn:
                    return (True, True)
        return (tailwind, shadcn)
    except Exception:
        return (False, False)
