"""GitHub Pages runner. Manual FCI uploads, persistent history, no pCloud calls."""
from __future__ import annotations

import argparse
import base64
import copy
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
import time
from urllib.parse import urlsplit
import uuid

import requests
import cloud_feed as core

HISTORY_BRANCH = "feed-history"
FCI_NAMES = {"BCACCA.json", "BCAHA.json", "BCMMA.json"}
STATE = "_state.json"
PUBLICATION = "publication.json"
SITE_NAMES = set(core.SEEDS) | {PUBLICATION, core.PROBE}


def json_bytes(value):
    return (json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + "\n").encode()


def parse_json(body, label):
    try:
        return json.loads(body.decode("utf-8-sig"))
    except (ValueError, UnicodeError):
        raise core.FeedError(f"{label}: JSON inválido.") from None


def sha(value):
    if not isinstance(value, str) or not re.fullmatch(r"[0-9a-f]{40}", value):
        raise core.FeedError("GitHub devolvió un identificador de versión inválido.")
    return value


class GitHub:
    def __init__(self):
        self.repository = os.environ.get("GITHUB_REPOSITORY", "")
        self.token = os.environ.get("GITHUB_TOKEN", "")
        if not re.fullmatch(r"[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+", self.repository) or not self.token:
            raise core.FeedError("Este modo requiere GITHUB_REPOSITORY y el GITHUB_TOKEN automático de Actions.")

    def call(self, method, path, data=None, missing_ok=False):
        try:
            response = requests.request(method, f"https://api.github.com/repos/{self.repository}/{path}",
                headers={"Authorization": f"Bearer {self.token}", "Accept": "application/vnd.github+json",
                         "X-GitHub-Api-Version": "2022-11-28"},
                json=data, timeout=(10, 60), allow_redirects=False)
            if response.status_code == 404 and missing_ok:
                return None
            if response.status_code not in (200, 201):
                raise core.FeedError(f"GitHub: HTTP {response.status_code}; revisar permisos, cuota o cambios simultáneos.")
            result = response.json()
        except (requests.RequestException, ValueError):
            raise core.FeedError("GitHub: error de red, certificado o respuesta JSON.") from None
        if not isinstance(result, dict):
            raise core.FeedError("GitHub: respuesta inesperada.")
        return result

    def head(self):
        ref = self.call("GET", f"git/ref/heads/{HISTORY_BRANCH}", missing_ok=True)
        return None if ref is None else sha(ref["object"]["sha"])

    def load(self):
        head = self.head()
        if head is None:
            return None, None
        commit = self.call("GET", f"git/commits/{head}")
        tree = self.call("GET", f"git/trees/{sha(commit['tree']['sha'])}")
        entries = tree.get("tree", [])
        expected = set(core.SEEDS) | {STATE}
        if tree.get("truncated") or len(entries) != len(expected) or {e.get("path") for e in entries} != expected:
            raise core.FeedError("Histórico GitHub incompleto o con archivos inesperados; no se sustituye por semillas.")
        files = {}
        for entry in entries:
            if entry.get("mode") != "100644" or entry.get("type") != "blob":
                raise core.FeedError("El histórico sólo admite archivos regulares.")
            blob = self.call("GET", f"git/blobs/{sha(entry['sha'])}")
            if blob.get("encoding") != "base64":
                raise core.FeedError("GitHub: codificación de archivo inesperada.")
            try:
                files[entry["path"]] = base64.b64decode(blob["content"].replace("\n", ""), validate=True)
            except (ValueError, TypeError):
                raise core.FeedError("GitHub: archivo histórico ilegible.") from None
        validate_history(files)
        return head, files

    def commit(self, files, expected_head):
        validate_history(files)
        if self.head() != expected_head:
            raise core.FeedError("El histórico cambió durante la ejecución; se cancela su escritura.")
        tree = self.call("POST", "git/trees", {"tree": [
            {"path": name, "mode": "100644", "type": "blob", "content": body.decode("utf-8")}
            for name, body in sorted(files.items())]})
        commit = self.call("POST", "git/commits", {
            "message": "Conservar cotizaciones publicadas y verificadas",
            "tree": sha(tree["sha"]), "parents": [expected_head] if expected_head else []})
        target = sha(commit["sha"])
        try:
            if expected_head is None:
                self.call("POST", "git/refs", {"ref": f"refs/heads/{HISTORY_BRANCH}", "sha": target})
            else:
                self.call("PATCH", f"git/refs/heads/{HISTORY_BRANCH}", {"sha": target, "force": False})
        except core.FeedError:
            # An uncertain response may have committed. Verify the exact ref, never retry blindly.
            if self.head() != target:
                raise
        if self.head() != target:
            raise core.FeedError("No se pudo confirmar la versión guardada del histórico.")
        return target


def validate_history(files):
    if set(files) != set(core.SEEDS) | {STATE}:
        raise core.FeedError("El lote histórico no contiene exactamente los archivos previstos.")
    state = parse_json(files[STATE], STATE)
    if not isinstance(state, dict) or set(state) != {"version", "applied_fci", "publication", "probe"} or state["version"] != 1:
        raise core.FeedError("Formato de estado del histórico no reconocido.")
    applied = state["applied_fci"]
    if not isinstance(applied, dict) or not set(applied) <= FCI_NAMES or any(not isinstance(h, str) or not re.fullmatch(r"[0-9a-f]{64}", h) for h in applied.values()):
        raise core.FeedError("Estado de cargas FCI inválido.")
    publication = state["publication"]
    if not isinstance(publication, dict) or set(publication) != {"generation", "generated_utc", "files"} or not re.fullmatch(r"[0-9a-f]{32}", str(publication["generation"])):
        raise core.FeedError("Manifest de publicación inválido.")
    reports = publication["files"]
    if not isinstance(reports, list) or len(reports) != len(core.SEEDS) or {r.get("file") for r in reports} != set(core.SEEDS):
        raise core.FeedError("Manifest de publicación incompleto.")
    for report in reports:
        name = report["file"]
        rows = core.decode(files[name], name)
        if report.get("sha256") != core.digest(core.encode(rows)) or report.get("count") != len(rows) or report.get("last") != rows[-1]["date"] or report.get("first") != rows[0]["date"]:
            raise core.FeedError(f"{name}: histórico distinto del manifest guardado.")
    core.validate(state["probe"], core.PROBE)
    return state


def safe_failure(exc):
    return str(exc) if isinstance(exc, core.FeedError) else f"Error {type(exc).__name__}; revisar el proveedor o la entrada."


def apply_fci(previous, applied, directory, failures=None):
    result, updated, notices = dict(previous), dict(applied), {}
    directory = Path(directory)
    if not directory.is_dir():
        raise core.FeedError("Falta la carpeta entradas-fci; revisar la instalación.")
    for path in directory.iterdir():
        if path.name in {"AGENTS.md", "README.md", ".gitkeep"}:
            continue
        if path.name not in FCI_NAMES or not path.is_file() or path.is_symlink():
            raise core.FeedError("entradas-fci admite sólo BCACCA.json, BCAHA.json y BCMMA.json; no subir TXT ni otros archivos.")
        try:
            rows = core.decode(path.read_bytes(), path.name)
            fingerprint = core.digest(core.encode(rows))
            if applied.get(path.name) == fingerprint:
                notices[path.name] = "carga ya incorporada; histórico conservado"
                continue
            merged = core.merge(previous[path.name], rows)
            core.validate(merged, path.name)
            core.require_coverage(previous[path.name], merged, path.name)
        except Exception as exc:
            if failures is None:
                raise
            failures[path.name] = safe_failure(exc)
            continue
        result[path.name] = merged
        updated[path.name] = fingerprint
        notices[path.name] = "carga manual incorporada; se preservaron fechas anteriores"
    return result, updated, notices


def refresh_series(previous, failures):
    """Isolate provider failures; fallback is always the validated prior series."""
    result, refreshed = dict(previous), set()
    sources = [(core.legacy.INSTRUMENTOS_QT, core.quicktrade),
               (core.legacy.DOLARAZO_DOLARES_CONFIG, core.dollars)]
    for config, _ in sources:
        if any(f"{symbol}.json" not in core.SEEDS for symbol in config):
            raise core.FeedError("Instrumento nuevo: actualizar la lista explícita de publicación primero.")
    today = core.TODAY()
    for config, fetch in sources:
        for symbol in config:
            name = f"{symbol}.json"
            try:
                rows = fetch(symbol, copy.deepcopy(previous[name]), today)
                core.validate(rows, name, today)
                core.require_coverage(previous[name], rows, name)
            except Exception as exc:
                failures[name] = safe_failure(exc)
                continue
            result[name] = rows
            refreshed.add(name)
    return result, refreshed


def site_from_history(files):
    state = validate_history(files)
    return {**{n: core.encode(core.decode(files[n], n)) for n in core.SEEDS},
            PUBLICATION: json_bytes(state["publication"]), core.PROBE: core.encode(state["probe"])}


def write_files(directory, files):
    directory.mkdir(parents=True, exist_ok=False)
    for name, body in files.items():
        if Path(name).name != name:
            raise core.FeedError("Nombre de salida inválido.")
        (directory / name).write_bytes(body)


def prepare(work, incoming, client=None, initialize=False):
    if work.exists():
        raise core.FeedError("La carpeta de trabajo ya existe; usar una nueva para evitar resultados antiguos.")
    seeds = core.local_seeds()
    base_head, old_files = (None, None) if client is None else client.load()
    if old_files is None:
        if client is not None and not initialize:
            raise core.FeedError("Aún no hay histórico GitHub; elegir Inicializar en la primera ejecución.")
        previous, applied = seeds, {}
    else:
        old_state = validate_history(old_files)
        previous = {name: core.decode(old_files[name], name) for name in core.SEEDS}
        for name in core.SEEDS:
            core.require_coverage(seeds[name], previous[name], name)
        applied = old_state["applied_fci"]
    # The previous snapshot was validated globally; only individual refreshes may fail.
    failures = {}
    candidates, applied, notices = apply_fci(previous, applied, incoming, failures)
    candidates, refreshed = refresh_series(candidates, failures)
    refreshed.update(name for name, notice in notices.items() if notice.startswith("carga manual incorporada"))
    if failures and not refreshed:
        raise core.FeedError("Ninguna serie pudo actualizarse; se conserva la publicación anterior. " +
                             "; ".join(f"{name}: {reason}" for name, reason in sorted(failures.items())))
    reports = []
    for name in core.SEEDS:
        rows = core.validate(candidates[name], name)
        core.require_coverage(previous[name], rows, name)
        source = notices.get(name, "FCI conservado sin nueva carga" if name in FCI_NAMES else
            ("descargado" if name[:-5] in core.legacy.INSTRUMENTOS_QT or name[:-5] in core.legacy.DOLARAZO_DOLARES_CONFIG else "histórico conservado"))
        report = {"file": name, "count": len(rows), "first": rows[0]["date"], "last": rows[-1]["date"],
                  "source": source, "sha256": core.digest(core.encode(rows)),
                  "outcome": "refreshed" if name in refreshed else "retained"}
        if name in failures:
            report.update(source="AVISO: actualización fallida; último histórico válido conservado",
                          outcome="retained_after_error", error=failures[name])
        reports.append(report)
    publication = {"generation": uuid.uuid4().hex, "generated_utc": datetime.now(timezone.utc).isoformat(), "files": reports}
    state = {"version": 1, "applied_fci": applied, "publication": publication,
             "probe": [{"date": core.TODAY().isoformat(), "close": uuid.uuid4().int % 1_000_000_000 + 1}]}
    history = {**{n: core.encode(candidates[n]) for n in core.SEEDS}, STATE: json_bytes(state)}
    validate_history(history)
    write_files(work / "next-history", history)
    write_files(work / "site", site_from_history(history))
    if old_files is not None:
        write_files(work / "previous-site", site_from_history(old_files))
    run = {"base_head": base_head, "local_only": client is None, "has_previous": old_files is not None,
           "generation": publication["generation"], "status": "validated_not_published", "warnings": failures}
    (work / "run.json").write_bytes(json_bytes(run))
    summary("Lote validado; todavía no publicado.\n" + "\n".join(
        f"- {r['file']}: {r['count']} precios; última fecha {r['last']}; {r['source']}" +
        (f". Motivo: {r['error']}" if "error" in r else "") for r in reports))
    for name, reason in sorted(failures.items()):
        message = f"{name}: se conserva el histórico anterior. {reason}"
        # Escape workflow command data, including unexpected multiline provider errors.
        message = message.replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")
        print(f"::warning title=Serie sin actualizar::{message}")
    if os.environ.get("GITHUB_OUTPUT"):
        with open(os.environ["GITHUB_OUTPUT"], "a", encoding="utf-8") as stream:
            stream.write(f"has_previous={str(run['has_previous']).lower()}\n")
    return run


def read_site(directory):
    entries = list(directory.iterdir())
    if {p.name for p in entries} != SITE_NAMES or any(not p.is_file() or p.is_symlink() for p in entries):
        raise core.FeedError("El sitio debe contener sólo las 17 cotizaciones, publication.json y la prueba sintética.")
    return {p.name: p.read_bytes() for p in entries}


def verify_site(directory, base_url, attempts=13, pause=5):
    u = urlsplit(base_url)
    if u.scheme != "https" or not u.hostname or not u.hostname.endswith(".github.io") or u.username or u.password or u.query or u.fragment or u.port:
        raise core.FeedError("Se requiere la URL HTTPS de GitHub Pages, sin parámetros.")
    base = base_url.rstrip("/") + "/"
    expected = read_site(directory)
    # The manifest changes every run, even when no market prices have changed.
    order = [PUBLICATION, core.PROBE, *core.SEEDS]
    for attempt in range(attempts):
        mismatches = []
        for name in order:
            try:
                body, _ = core.download_bytes(base + name)
                if parse_json(body, name) != parse_json(expected[name], name):
                    mismatches.append(name)
            except core.FeedError:
                mismatches.append(name)
            if name == PUBLICATION and mismatches:
                break
        if not mismatches:
            summary("Todas las URL fijas verificadas sin parámetros de caché.")
            return
        if attempt + 1 < attempts:
            time.sleep(pause)
    raise core.FeedError("Pages todavía no entrega la versión esperada en las URL fijas: " + ", ".join(mismatches))


def commit_history(work, client):
    run = parse_json((work / "run.json").read_bytes(), "run")
    if run["local_only"] or not (work / "verified.json").is_file():
        raise core.FeedError("Se requiere publicación remota verificada antes de guardar el histórico.")
    verified = parse_json((work / "verified.json").read_bytes(), "verificación")
    if verified.get("generation") != run["generation"]:
        raise core.FeedError("La verificación pertenece a otra ejecución.")
    paths = list((work / "next-history").iterdir())
    if any(not p.is_file() or p.is_symlink() for p in paths):
        raise core.FeedError("Histórico preparado inválido.")
    files = {p.name: p.read_bytes() for p in paths}
    if validate_history(files)["publication"]["generation"] != run["generation"] or site_from_history(files) != read_site(work / "site"):
        raise core.FeedError("El histórico preparado cambió después de la verificación.")
    revision = client.commit(files, run["base_head"])
    run.update(status="published_verified", history_commit=revision)
    (work / "run.json").write_bytes(json_bytes(run))
    pending = [r["file"] for r in validate_history(files)["publication"]["files"]
               if r.get("outcome") == "retained_after_error"]
    if pending:
        summary("published_verified — PUBLICACIÓN CON AVISOS: las series válidas se publicaron y verificaron. "
                "Conservan su histórico anterior por un error: " + ", ".join(pending) + ". Revisar sus motivos en el resumen de preparación.")
    else:
        summary("published_verified: publicación comprobada e histórico guardado. Ya se puede actualizar PP.")


def summary(message):
    print(message)
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8") as stream:
            stream.write(message + "\n\n")


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=["stage", "verify", "verify-previous", "commit"])
    parser.add_argument("--work", type=Path, required=True)
    parser.add_argument("--incoming", type=Path, default=core.ROOT / "entradas-fci")
    parser.add_argument("--local", action="store_true")
    parser.add_argument("--initialize", action="store_true")
    args = parser.parse_args(argv)
    try:
        if args.mode == "stage":
            prepare(args.work, args.incoming, None if args.local else GitHub(), args.initialize)
        elif args.mode.startswith("verify"):
            previous = args.mode == "verify-previous"
            verify_site(args.work / ("previous-site" if previous else "site"), os.environ.get("PAGES_BASE_URL", ""))
            if not previous:
                run = parse_json((args.work / "run.json").read_bytes(), "run")
                (args.work / "verified.json").write_bytes(json_bytes({"generation": run["generation"]}))
            else:
                summary("Publicación anterior restaurada y verificada; esta actualización sigue marcada como fallida.")
        else:
            commit_history(args.work, GitHub())
        return 0
    except Exception as exc:
        message = str(exc) if isinstance(exc, core.FeedError) else f"Error {type(exc).__name__}; revisar entradas, dependencias o respuesta del proveedor."
        summary("ERROR: " + message)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
