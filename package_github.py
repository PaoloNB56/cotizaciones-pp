"""Build the reviewed GitHub installation ZIP locally; never upload it."""
from zipfile import ZipFile, ZIP_DEFLATED

from cloud_feed import ROOT, SEEDS, local_seeds

FILES = [
    "README.md", "LEEME-NUBE.md", "AGENTS.md", ".gitignore",
    "github_feed.py", "cloud_feed.py", "update_bonos.py", "fondos_txt_a_json.py",
    "test_cloud_feed.py", "test_github_feed.py", "requirements-cloud.in", "package_github.py",
    ".github/AGENTS.md", ".github/workflows/cotizaciones.yml", ".cloud-work/AGENTS.md",
    "entradas-fci/AGENTS.md", "entradas-fci/README.md", "FCI/AGENTS.md",
    *SEEDS.values(),
]


def main():
    local_seeds()
    target = ROOT / "pp-feed-github.zip"
    temporary = ROOT / "pp-feed-github.zip.tmp"
    if len(set(FILES)) != len(FILES):
        raise ValueError("Duplicate installation entries")
    with ZipFile(temporary, "w", ZIP_DEFLATED) as archive:
        for name in FILES:
            source = ROOT / name
            if source.is_symlink() or not source.is_file():
                raise ValueError("Installation source must be a regular file")
            archive.write(source, name)
    with ZipFile(temporary) as archive:
        if archive.testzip() or set(archive.namelist()) != set(FILES):
            raise ValueError("Invalid package")
        for name in FILES:
            if archive.read(name) != (ROOT / name).read_bytes():
                raise ValueError("Package differs from source")
    temporary.replace(target)
    print(f"Paquete local: {target}; {len(FILES)} archivos; {target.stat().st_size} bytes. No publicado.")


if __name__ == "__main__":
    main()
