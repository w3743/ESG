"""Download, verify and reassemble the B09 GGUF release (Python 3.10+)."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import sys
import urllib.request

CHUNK = 8 * 1024 * 1024


def verify(path, size, expected_hash):
    if not path.is_file() or path.stat().st_size != size:
        return False
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(CHUNK), b''):
            digest.update(chunk)
    return digest.hexdigest() == expected_hash


def restore(manifest, output_dir, merge_only=False):
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    entries = [manifest] + manifest['parts']
    names = [manifest['filename']] + [part['name'] for part in manifest['parts']]
    if len(set(names)) != len(names):
        raise ValueError('Duplicate filenames in manifest')
    for name, entry in zip(names, entries):
        if not name or name in ('.', '..') or '/' in name or '\\' in name or ':' in name:
            raise ValueError('Unsafe filename in manifest')
        if not isinstance(entry['size_bytes'], int) or entry['size_bytes'] <= 0:
            raise ValueError('Invalid size in manifest')
    if sum(part['size_bytes'] for part in manifest['parts']) != manifest['size_bytes']:
        raise ValueError('Part sizes do not match full model size')
    output = output_dir / manifest['filename']
    if verify(output, manifest['size_bytes'], manifest['sha256']):
        print('Model already verified:', output)
        return output
    if output.exists():
        raise ValueError(f'Existing output failed verification; move it aside before retrying: {output}')
    for part in manifest['parts']:
        target = output_dir / part['name']
        if verify(target, part['size_bytes'], part['sha256']):
            print('Verified part:', target.name, flush=True)
            continue
        if merge_only:
            raise ValueError(f'Missing or corrupt part: {target}')
        temporary = target.with_name(target.name + '.download')
        print('Downloading:', target.name, flush=True)
        request = urllib.request.Request(part['url'], headers={'User-Agent': 'ESG-B09-model-downloader'})
        with urllib.request.urlopen(request, timeout=120) as response, temporary.open('wb') as stream:
            shutil.copyfileobj(response, stream, CHUNK)
        if not verify(temporary, part['size_bytes'], part['sha256']):
            raise ValueError(f'Download failed verification: {temporary}')
        os.replace(temporary, target)
    temporary = output.with_name(output.name + '.assembling')
    digest = hashlib.sha256()
    total = 0
    with temporary.open('wb') as merged:
        for part in manifest['parts']:
            with (output_dir / part['name']).open('rb') as stream:
                for chunk in iter(lambda: stream.read(CHUNK), b''):
                    merged.write(chunk)
                    digest.update(chunk)
                    total += len(chunk)
    if total != manifest['size_bytes'] or digest.hexdigest() != manifest['sha256']:
        raise ValueError(f'Assembled model failed verification: {temporary}')
    os.replace(temporary, output)
    print('Model SHA256 verified:', digest.hexdigest(), flush=True)
    print('Ready:', output, flush=True)
    return output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', type=Path, default=Path('downloaded-models'))
    parser.add_argument('--merge-only', action='store_true', help='Use local parts without downloading')
    args = parser.parse_args()
    manifest = json.loads(Path(__file__).with_name('manifest.json').read_text(encoding='utf-8'))
    try:
        restore(manifest, args.output_dir, args.merge_only)
    except (OSError, ValueError) as error:
        print(f'Error: {error}', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
