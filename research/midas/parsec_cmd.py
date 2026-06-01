"""Fetch PARSEC isochrones from the Padova CMD 3.9 web service."""

from __future__ import annotations

import re
import ssl
import urllib.parse
import urllib.request
from pathlib import Path

CMD_URL = "https://stev.oapd.inaf.it/cgi-bin/cmd/cmd_3.9"
CMD_TMP_BASE = "https://stev.oapd.inaf.it/tmp/"

# Ages aligned with legacy YY isochrones on the website.
TARGET_AGES_GYR: dict[str, float] = {
    "0.080": 7.90309,  # 80 Myr
    "0.100": 8.0,
    "0.200": 8.301,
    "0.400": 8.60206,
    "0.600": 8.77815,
    "1.000": 9.0,
}

DEFAULT_Z = 0.0152  # solar scaled-solar for PARSEC v1.2S


def _urlopen_text(url: str, *, data: bytes | None = None, method: str = "GET") -> str:
    req = urllib.request.Request(url, data=data, method=method)
    for ctx in (ssl.create_default_context(), ssl._create_unverified_context()):  # noqa: SLF001
        try:
            with urllib.request.urlopen(req, timeout=120, context=ctx) as resp:
                return resp.read().decode("utf-8", errors="replace")
        except urllib.error.URLError:
            continue
    raise RuntimeError(f"Failed to fetch {url}")


def _post_cmd(form: dict[str, str]) -> str:
    data = urllib.parse.urlencode(form).encode("utf-8")
    html = _urlopen_text(CMD_URL, data=data, method="POST")
    match = re.search(r'href=\.\./tmp/(output\d+\.dat)', html)
    if not match:
        if "errorwarning" in html:
            err = re.search(r"errorwarning[^>]*><b>Error:</b>\s*([^<]+)", html, re.I)
            msg = err.group(1).strip() if err else "CMD returned form instead of output"
            raise RuntimeError(f"CMD request failed: {msg}")
        raise RuntimeError("CMD response did not contain output file link")
    dat_url = f"{CMD_TMP_BASE}{match.group(1)}"
    return _urlopen_text(dat_url)


def fetch_isochrone_table(
    *,
    log_age: float,
    z: float = DEFAULT_Z,
    log_age_step: float = 0.0,
) -> str:
    """Download a PARSEC v1.2S isochrone table (UBV, intrinsic Av=0)."""
    form = {
        "submit_form": "Submit",
        "cmd_version": "3.9",
        "track_parsec": "parsec_CAF09_v1.2S",
        "track_colibri": "no",
        "track_postagb": "no",
        "track_omegai": "0.00",
        "n_inTPC": "10",
        "eta_reimers": "0.2",
        "kind_interp": "1",
        "kind_postagb": "-1",
        "photsys_file": "tab_mag_odfnew/tab_mag_ubvrijhk.dat",
        "photsys_version": "odfnew",
        "dust_sourceM": "dpmod60alox40",
        "dust_sourceC": "AMCSIC15",
        "kind_LPV": "3",
        "imf_file": "tab_imf/imf_kroupa_orig.dat",
        "isoc_isagelog": "1",
        "isoc_lagelow": f"{log_age:.5f}",
        "isoc_lageup": f"{log_age:.5f}",
        "isoc_dlage": f"{log_age_step:.5f}",
        "isoc_isometlog": "0",
        "isoc_zlow": f"{z:.4f}",
        "isoc_zup": f"{z:.4f}",
        "isoc_dz": "0.0",
        "output_kind": "0",
        "output_gzip": "0",
        "extinction_av": "0.0",
        "extinction_coeff": "constant",
        "extinction_curve": "cardelli",
    }
    return _post_cmd(form)


def fetch_all_target_ages(z: float = DEFAULT_Z) -> str:
    """Fetch each target age and concatenate into one CMD-style table."""
    chunks: list[str] = []
    for age_key, log_age in TARGET_AGES_GYR.items():
        table = fetch_isochrone_table(log_age=log_age, z=z)
        chunks.append(f"# --- age(Gyr)={age_key} logAge={log_age:.5f} ---")
        chunks.extend(line for line in table.splitlines() if line.strip())
    return "\n".join(chunks) + "\n"


def parse_isochrone_table(text: str) -> dict[float, list[tuple[float, float]]]:
    """Parse CMD output into {log_age: [(mv, bv), ...]}."""
    blocks: dict[float, list[tuple[float, float]]] = {}
    for line in text.splitlines():
        if not line.strip() or line.startswith("#"):
            continue
        parts = line.split()
        if len(parts) < 14:
            continue
        try:
            log_age = float(parts[2])
            b_mag = float(parts[12])
            v_mag = float(parts[13])
        except ValueError:
            continue
        if v_mag > 14 or v_mag < -0.5 or b_mag - v_mag > 2.5:
            continue
        blocks.setdefault(log_age, []).append((v_mag, b_mag - v_mag))
    return blocks


def pick_nearest_age(blocks: dict[float, list[tuple[float, float]]], log_age: float) -> list[tuple[float, float]]:
    if not blocks:
        return []
    key = min(blocks.keys(), key=lambda k: abs(k - log_age))
    return blocks[key]


def save_table(text: str, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text)
