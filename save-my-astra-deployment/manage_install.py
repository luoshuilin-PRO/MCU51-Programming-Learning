import argparse, datetime, hashlib, json, shutil, sys, tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SOURCE = Path(__file__).resolve().parent / 'source/save-my-astra-main'
if not SOURCE.exists():
    SOURCE = ROOT / 'work/source/save-my-astra-main'
sys.path.insert(0, str(SOURCE))
sys.path.insert(0, str(Path(__file__).resolve().parent / 'python-deps'))
from eval.install_merge import write_install, verify_install

FILES = ['config.toml', 'AGENTS.md', 'agents/luna-max-worker.toml', 'skills/save-my-astra/SKILL.md']

def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None

def install(home):
    home.mkdir(parents=True, exist_ok=True)
    backup = home / 'backups' / ('save-my-astra-' + datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
    backup.mkdir(parents=True)
    manifest = {'home': str(home.resolve()), 'files': {}}
    for name in FILES:
        src = home / name
        manifest['files'][name] = {'before': digest(src)}
        if src.exists():
            dst = backup / name
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
    before = tomllib.loads((home / 'config.toml').read_text(encoding='utf-8')) if (home / 'config.toml').exists() else {}
    try:
        write_install(home, 'astra-luna')
        # Preserve existing global instructions, which upstream replaces.
        old = backup / 'AGENTS.md'
        if old.exists():
            p = home / 'AGENTS.md'
            p.write_text(old.read_text(encoding='utf-8') + '\n\n' + p.read_text(encoding='utf-8'), encoding='utf-8')
        errors, summary = verify_install(home, 'astra-luna')
        after = tomllib.loads((home / 'config.toml').read_text(encoding='utf-8'))
        for key in set(before) - {'model', 'model_reasoning_effort', 'agents', 'features'}:
            assert before[key] == after[key], 'Unrelated config changed: ' + key
        # Preserve unrelated agents and feature fields removed by upstream section replacement.
        for section in ['agents', 'features']:
            original = before.get(section, {})
            current = after.get(section, {})
            for key, value in original.items():
                if section == 'agents' and key in {'enabled', 'default_subagent_model', 'default_subagent_reasoning_effort', 'max_concurrent_threads_per_session'}:
                    continue
                if section == 'features' and key == 'multi_agent_v2':
                    assert all(current.get(key, {}).get(k) == v for k,v in value.items() if k != 'hide_spawn_agent_metadata'), 'Existing feature settings would be lost'
                else:
                    assert current.get(key) == value, 'Existing settings would be lost: ' + section + '.' + key
        assert not errors, errors
        for name in FILES:
            manifest['files'][name]['installed'] = digest(home / name)
        print(json.dumps(summary))
    except BaseException:
        for name, state in manifest['files'].items():
            p = home / name
            if state['before'] is None:
                p.unlink(missing_ok=True)
            else:
                shutil.copy2(backup / name, p)
        raise
    finally:
        (backup / 'manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
    print('BACKUP=' + str(backup))
    return backup

def rollback(backup):
    manifest = json.loads((backup / 'manifest.json').read_text(encoding='utf-8'))
    home = Path(manifest['home'])
    for name, state in manifest['files'].items():
        assert digest(home / name) == state['installed'], 'File changed after install; refusing to overwrite: ' + name
    for name, state in manifest['files'].items():
        p = home / name
        assert home.resolve() in p.resolve().parents
        if state['before'] is None:
            p.unlink(missing_ok=True)
        else:
            shutil.copy2(backup / name, p)
        assert digest(p) == state['before']
    print('ROLLBACK_OK: all original file bytes restored; newly installed files removed')

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('action', choices=['install', 'rollback', 'test'])
    parser.add_argument('path', type=Path)
    args = parser.parse_args()
    if args.action == 'rollback':
        rollback(args.path)
    elif args.action == 'install':
        install(args.path)
    else:
        rollback(install(args.path))

