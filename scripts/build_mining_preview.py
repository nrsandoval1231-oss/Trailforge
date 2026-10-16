"""Export the product UI with frozen existing-engine results; no alternative backend."""
from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from importlib.resources import files
from pathlib import Path

from athena_procurement_arena.mining import load_project, load_supplier, match_supplier, qualify, render_report


def build(output: Path, inputs: list[Path], supplier_path: Path | None = None) -> None:
    supplier = load_supplier(supplier_path)
    projects = [load_project(path) for path in inputs]  # Validate rights before writing.
    output.mkdir(parents=True, exist_ok=False)
    assets = files('athena_procurement_arena').joinpath('ui_assets')
    for asset in assets.iterdir():
        if asset.is_file():
            (output / asset.name).write_bytes(asset.read_bytes())
    (output / 'api').mkdir()
    data = {'supplier': asdict(supplier), 'projects': [
        {'index': i, 'project': project, 'evaluations': [
            {'requirement_id': req['requirement_id'], 'qualification': qualify(req),
             'match': match_supplier(req, supplier, location=project['project']['location']['value'])}
            for req in project['requirements']]}
        for i, project in enumerate(projects)]}
    (output / 'api/mining').write_text(json.dumps(data, indent=2) + '\n', encoding='utf-8')
    page = (output / 'index.html').read_text(encoding='utf-8')
    page = page.replace('<body>', '<body><div class="preview-banner">Interactive snapshot · '
                        'Engine results frozen at export. Synthetic records are labeled. '
                        'Research workbench runs in the Python application.</div>')
    page = page.replace('<a href="/workbench">Research workbench</a>', '<span>Read-only interactive snapshot</span>')
    (output / 'index.html').write_text(page, encoding='utf-8')
    js = (output / 'product.js').read_text(encoding='utf-8')
    js = js.replace('"/mining/" + item.p.index', '"/mining/" + item.p.index + "/"')
    (output / 'product.js').write_text(js, encoding='utf-8')
    mining = output / 'mining'
    mining.mkdir()
    (mining / 'style.css').write_bytes(assets.joinpath('style.css').read_bytes())
    links = []
    for i, project in enumerate(projects):
        target = mining / str(i)
        target.mkdir()
        (target / 'index.html').write_text(render_report(project, supplier), encoding='utf-8')
        (target / 'style.css').write_bytes(assets.joinpath('style.css').read_bytes())
        links.append(f'<li><a href="{i}/">Imported report {i + 1}</a></li>')
    (mining / 'index.html').write_text('<!doctype html><html lang="en"><meta charset="utf-8">'
                                     '<title>Frozen mining reports</title><a href="/">Product workspace</a>'
                                     '<h1>Frozen mining reports</h1><ul>' + ''.join(links) + '</ul>', encoding='utf-8')


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--mining-input', type=Path, action='append', default=[])
    parser.add_argument('--mining-supplier', type=Path)
    args = parser.parse_args()
    build(args.output, args.mining_input, args.mining_supplier)


if __name__ == '__main__':
    main()
