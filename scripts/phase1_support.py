"""Small manifest helpers; never read market data or mutate existing runs."""
from pathlib import Path
import datetime as dt
import hashlib
import json

ROOT = Path(__file__).resolve().parents[1]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def record_run(prefix, metadata):
    run_id = dt.datetime.now(dt.timezone.utc).strftime(prefix + '_%Y%m%dT%H%M%SZ')
    directory = ROOT / 'runs' / run_id
    directory.mkdir(parents=True, exist_ok=False)
    metadata = dict(metadata, run_id=run_id, captured_utc=dt.datetime.now(dt.timezone.utc).isoformat())
    path = directory / 'metadata.json'
    path.write_text(json.dumps(metadata, indent=2, allow_nan=False) + '\n', encoding='utf-8', newline='\n')
    index_path = ROOT / 'manifests/run_index.json'
    index = json.loads(index_path.read_text())
    index.append({'run_id': run_id, 'metadata_path': path.relative_to(ROOT).as_posix(),
                  'metadata_sha256': sha(path), 'status': metadata.get('status', 'completed'),
                  'is_current_checkpoint_run': True})
    index_path.write_text(json.dumps(index, indent=2) + '\n', encoding='utf-8', newline='\n')
    return run_id
