"""Restore uploaded annual Parquets and checkpoint ZIPs without API calls."""
from pathlib import Path
import hashlib
import json
import shutil
import zipfile

ROOT = Path(__file__).resolve().parents[1]

def sha(path):
    h = hashlib.sha256()
    with path.open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()

def main():
    archives = ["ESPEF_Checkpoints_2021.zip", "ESPEF_Checkpoints_2022.zip",
                "ESPEF_Checkpoints_2023_PARTIAL.zip"]
    plan = []
    for year in (2021, 2022):
        audit = json.loads((ROOT / f"data/audits/espef_audit_{year}.json").read_text())
        for item in audit["files"].values():
            target = ROOT / item["path"]
            source = target if target.exists() else ROOT / target.name
            if not source.is_file():
                raise RuntimeError(f"Missing uploaded file: {target.name}")
            if sha(source) != item["sha256"]:
                raise RuntimeError(f"Checksum mismatch: {source.name}")
            plan.append((source, target))
    for name in archives:
        path = ROOT / name
        if not path.is_file():
            raise RuntimeError(f"Missing uploaded archive: {name}")
        with zipfile.ZipFile(path) as archive:
            for item in archive.infolist():
                rel = Path(item.filename)
                if rel.parts and rel.parts[0] == "ESPEF":
                    rel = Path(*rel.parts[1:])
                if rel == Path("config/openalex.json"):
                    if json.loads(archive.read(item)) != json.loads((ROOT / rel).read_text()):
                        raise RuntimeError("Archived configuration differs from current configuration")
                    continue
                if rel.is_absolute() or ".." in rel.parts or rel.parts[:2] != ("data", "checkpoints"):
                    raise RuntimeError(f"Unexpected archive entry in {name}")
    for source, target in plan:
        target.parent.mkdir(parents=True, exist_ok=True)
        if source != target:
            shutil.move(str(source), str(target))
    for name in archives:
        with zipfile.ZipFile(ROOT / name) as archive:
            for item in archive.infolist():
                if item.is_dir():
                    continue
                rel = Path(item.filename)
                if rel.parts[0] == "ESPEF":
                    rel = Path(*rel.parts[1:])
                if rel == Path("config/openalex.json"):
                    continue
                target = ROOT / rel
                target.parent.mkdir(parents=True, exist_ok=True)
                if target.exists():
                    with archive.open(item) as f:
                        h = hashlib.sha256()
                        for block in iter(lambda: f.read(1024 * 1024), b""):
                            h.update(block)
                    if sha(target) != h.hexdigest():
                        raise RuntimeError(f"Existing checkpoint differs: {rel}; retained without overwrite")
                    continue
                with archive.open(item) as src, target.open("wb") as dest:
                    shutil.copyfileobj(src, dest)
        print(f"Restored {name}", flush=True)
    print("RESTORE OK: annual Parquet checksums verified; checkpoints restored. No download started.")

if __name__ == "__main__":
    main()
