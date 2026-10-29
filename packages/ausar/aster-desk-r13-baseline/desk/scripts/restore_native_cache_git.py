"""Stream-verify or restore a sealed R11 cache phase from an immutable Git commit.

Requires ordinary configured gh auth. No credentials are read by this program.
The default is verification only: original archived PKLs are never unpickled.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import subprocess
import tarfile
from pathlib import Path

REPOSITORY = 'dwj9ddyvf6-hub/quant-research-backup'


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


def api(endpoint):
    process = subprocess.run(['gh', 'api', endpoint], capture_output=True)
    require(process.returncode == 0, 'Git API request failed; stderr SHA256=' + hashlib.sha256(process.stderr).hexdigest())
    return json.loads(process.stdout)


def raw_json(git_sha):
    process = subprocess.run(['gh', 'api', f'repos/{REPOSITORY}/git/blobs/{git_sha}',
                              '--header', 'Accept: application/vnd.github.raw+json'], capture_output=True)
    require(process.returncode == 0, 'Git raw JSON request failed')
    data = process.stdout
    require(hashlib.sha1(f'blob {len(data)}\0'.encode() + data).hexdigest() == git_sha, 'JSON Git object identity')
    return json.loads(data)


def resolve(tree, path):
    for number, component in enumerate(path.split('/')):
        entries = {entry['path']: entry for entry in api(f'repos/{REPOSITORY}/git/trees/{tree}')['tree']}
        require(component in entries, 'Missing pinned commit path: ' + path)
        entry = entries[component]
        if number < len(path.split('/')) - 1:
            require(entry['type'] == 'tree', 'Pinned path ancestor not a tree')
            tree = entry['sha']
    require(entry['type'] == 'blob', 'Pinned path not a blob')
    return entry['sha']


class PartStream:
    def __init__(self, parts):
        self.parts = parts
        self.next = 0
        self.process = None
        self.total = 0
        self.digest = hashlib.sha256()
        self.closed_parts = []

    def start(self):
        if self.next >= len(self.parts):
            return False
        self.part = self.parts[self.next]
        require(self.part['partNumber'] == self.next + 1, 'Part numbering gap')
        self.next += 1
        self.size = 0
        self.part_hash = hashlib.sha256()
        self.git_hash = hashlib.sha1(f"blob {self.part['bytes']}\0".encode())
        self.process = subprocess.Popen(['gh', 'api', f"repos/{REPOSITORY}/git/blobs/{self.part['gitBlobSha']}",
                                         '--header', 'Accept: application/vnd.github.raw+json'],
                                        stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        return True

    def finish(self):
        error = self.process.stderr.read()
        code = self.process.wait()
        require(code == 0, 'Part download failure; stderr SHA256=' + hashlib.sha256(error).hexdigest())
        require(self.size == self.part['bytes'] and self.part_hash.hexdigest() == self.part['sha256']
                and self.git_hash.hexdigest() == self.part['gitBlobSha'], 'Part byte/Git/SHA256 mismatch')
        self.closed_parts.append(self.part['partNumber'])
        self.process = None

    def read(self, count=-1):
        require(count >= 0, 'Unbounded streaming read prohibited')
        chunks = []
        remaining = count
        while remaining:
            if self.process is None and not self.start():
                break
            block = self.process.stdout.read(min(remaining, 256 * 1024))
            if not block:
                self.finish()
                continue
            self.size += len(block)
            self.total += len(block)
            self.part_hash.update(block)
            self.git_hash.update(block)
            self.digest.update(block)
            chunks.append(block)
            remaining -= len(block)
        return b''.join(chunks)

    def abort(self):
        if self.process is not None:
            self.process.terminate()
            self.process.wait()
            self.process = None


def verify_or_restore(commit, prefix, phase, output=None):
    require(len(commit) == 40 and all(c in '0123456789abcdef' for c in commit), 'Immutable full Git commit SHA required')
    require(not prefix.startswith('/') and '..' not in Path(prefix).parts, 'Unsafe prefix')
    tree = api(f'repos/{REPOSITORY}/git/commits/{commit}')['tree']['sha']
    path = prefix + '/' + phase
    index_sha = resolve(tree, path + '/reconstruction-index.json')
    manifest_sha = resolve(tree, path + '/member-manifest.json')
    index = raw_json(index_sha)
    manifest = raw_json(manifest_sha)
    require(index['manifestBlob']['gitBlobSha'] == manifest_sha, 'Index manifest binding')
    require(index['phase'] == manifest['phase'] == phase, 'Phase identity mismatch')
    for part in index['parts']:
        require(resolve(tree, path + '/parts/' + part['name']) == part['gitBlobSha'], 'Part not bound to pinned commit')
    members = {member['archivePath']: member for member in manifest['members']}
    require(len(members) == len(manifest['members']), 'Duplicate manifest member')
    target = Path(output).resolve() if output else None
    if target:
        require(not target.exists(), 'Restore destination must be new and absent')
        target.mkdir(parents=True)
    stream = PartStream(index['parts'])
    visited = set()
    try:
        with tarfile.open(fileobj=stream, mode='r|') as package:
            for entry in package:
                name = entry.name
                require(not name.startswith('/') and '..' not in Path(name).parts and entry.isfile(), 'Unsafe TAR entry')
                require(name not in visited, 'Duplicate TAR member')
                require(entry.uid == entry.gid == entry.mtime == 0 and entry.mode == 0o644, 'TAR metadata mismatch')
                visited.add(name)
                expected = index['manifestBlob'] if name == 'member-manifest.json' else members.get(name)
                require(expected is not None and entry.size == expected['bytes'], 'Unexpected member or byte count')
                h = hashlib.sha256()
                destination = None
                if target:
                    local = target / name
                    local.parent.mkdir(parents=True, exist_ok=True)
                    destination = local.open('xb')
                try:
                    source = package.extractfile(entry)
                    while block := source.read(256 * 1024):
                        h.update(block)
                        if destination:
                            destination.write(block)
                finally:
                    if destination:
                        destination.close()
                require(h.hexdigest() == expected['sha256'], 'Member SHA256 mismatch: ' + name)
        while stream.read(256 * 1024):
            pass  # Consume closed TAR padding and independently finish every remote part.
        require(visited == set(members) | {'member-manifest.json'}, 'TAR member denominator mismatch')
        require(stream.total == index['tarBytes'] and stream.digest.hexdigest() == index['tarSha256'], 'Whole TAR byte/SHA256 mismatch')
    except BaseException:
        stream.abort()
        raise
    return {'status': 'PASS', 'commit': commit, 'phase': phase, 'members': len(members),
            'parts': len(stream.closed_parts), 'tarBytes': stream.total, 'tarSha256': stream.digest.hexdigest(),
            'mode': 'RESTORE' if target else 'VERIFY_ONLY', 'financialExperiments': 0, 'pickleInterpretations': 0}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--commit', required=True)
    parser.add_argument('--prefix', required=True)
    parser.add_argument('--phase', required=True, choices=['predictive-information-cache', 'native-inputs', 'native-features'])
    parser.add_argument('--output', help='Absent means stream verification only. Restore requires a new absent directory.')
    args = parser.parse_args()
    print(json.dumps(verify_or_restore(args.commit, args.prefix, args.phase, args.output)))
