"""Bundle checked generated results with publication and contributor metadata.

Scientific artifacts stay unchanged. Contributor names can come from an exact
local Git commit or from the explicit, reviewable history manifest.
"""
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[1]


def read_viewer(path):
    text = (ROOT / path).read_text()
    if path.endswith('.js'):
        text = text.removeprefix('window.WARP_DEFAULT_RESULT = ').strip().removesuffix(';')
    return json.loads(text)


def resolve_author(metadata):
    if metadata.get('git_commit'):
        revision = metadata['git_commit']
        if not re.fullmatch(r'[a-fA-F0-9]{40}|[a-fA-F0-9]{64}', revision):
            raise ValueError('Author attribution requires a full Git commit hash.')
        name = subprocess.check_output(
            ['git', 'show', '--no-patch', '--format=%an', revision, '--'],
            cwd=ROOT, text=True).strip()
        return {'name': name, 'git_commit': revision, 'source': 'Git commit author'}
    if not isinstance(metadata.get('name'), str) or not metadata['name'].strip():
        raise ValueError('Every evaluation needs a named author or an exact Git commit.')
    return dict(metadata)


def main():
    manifest = json.loads((ROOT / 'records/history.json').read_text())
    entries = []
    for row in manifest['evaluations']:
        report = json.loads((ROOT / row['report_path']).read_text())
        artifact = read_viewer(row['viewer_path'])
        for field in ['candidate', 'energy', 'benchmark']:
            if report[field] != artifact[field]:
                raise ValueError(f'{field} mismatch: {row["report_path"]}')
        if report['provenance']['evaluator_source_sha256'] != artifact['provenance']['evaluator_source_sha256']:
            raise ValueError(f'Evaluator mismatch: {row["report_path"]}')
        author = resolve_author(row['author'])
        entries.append({'id': row['id'], 'title': author['name'], 'author': author,
                        'kind': row['kind'], 'evaluated_utc': report['provenance']['created_utc'],
                        'report_path': row['report_path'], 'artifact': artifact})
    encoded = []
    for row, entry in zip(manifest['evaluations'], entries):
        if row['viewer_path'] == 'web/default-result.js':
            metadata = {key: value for key, value in entry.items() if key != 'artifact'}
            encoded.append(json.dumps(metadata, separators=(',', ':'))[:-1] + ',"artifact":window.WARP_DEFAULT_RESULT}')
        else:
            encoded.append(json.dumps(entry, separators=(',', ':'), allow_nan=False))
    publications = json.dumps(manifest['publications'], separators=(',', ':'), allow_nan=False)
    (ROOT / 'web/history.js').write_text(
        'window.WARP_PUBLICATIONS = ' + publications + ';\n' +
        'window.WARP_BUNDLED_HISTORY = [' + ','.join(encoded) + '];\n')
    print(f'Bundled {len(entries)} attributed evaluations and {len(manifest["publications"])} publication reference.')


if __name__ == '__main__':
    main()
