"""Bundle the analysis engine for the web app (docs/app/).

GitHub Pages serves only docs/, so the Python code and the exchange-rate tables the browser runs are
zipped into docs/app/engine.zip, laid out as in the repo. The zip is byte-for-byte reproducible, and
tests/test_web.py fails when it is out of date: run this after changing src/, app/web.py,
app/i18n.py, app/offers.py or data/.

Usage:  python scripts/build_web.py
"""
from __future__ import annotations

import hashlib
import io
import re
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "docs" / "app" / "engine.zip"
WORKER = ROOT / "docs" / "app" / "py-worker.js"


def sources() -> list[Path]:
    files = [ROOT / "app" / n for n in ("web.py", "i18n.py", "offers.py")]
    files += sorted((ROOT / "src").glob("*.py"))
    files += sorted((ROOT / "data" / "fx").glob("*.csv"))
    files += [ROOT / "data" / "sample" / "sample_statement.csv", ROOT / "data" / "sample" / "sample_prices.csv"]
    return files


def build() -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for f in sources():
            info = zipfile.ZipInfo(f.relative_to(ROOT).as_posix(), date_time=(1980, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            # all text: line endings as committed, so a Windows checkout builds the same bytes
            data = f.read_bytes().replace(b"\r\n", b"\n")
            z.writestr(info, data)
    return buf.getvalue()


def version(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()[:10]


def main() -> None:
    data = build()
    OUT.write_bytes(data)
    # the worker asks for engine.zip?v=<hash>, so browsers drop a cached old engine
    js = WORKER.read_text(encoding="utf-8")
    js = re.sub(r'const ENGINE_VERSION = "[^"]*";', f'const ENGINE_VERSION = "{version(data)}";', js)
    WORKER.write_text(js, encoding="utf-8")
    print(f"{OUT.relative_to(ROOT)}: {len(data) / 1024:.0f} KB, version {version(data)}")


if __name__ == "__main__":
    main()
