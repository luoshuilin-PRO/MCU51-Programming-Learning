"""Run once next to manage_install.py; download upstream and isolated dependencies."""
import hashlib, io, json, sys, urllib.request, zipfile
from pathlib import Path

root = Path(__file__).resolve().parent
def unpack(data, target):
    target.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(io.BytesIO(data)) as archive:
        for item in archive.infolist():
            assert target.resolve() in (target / item.filename).resolve().parents
        archive.extractall(target)

data = urllib.request.urlopen('https://codeload.github.com/fengxiaohu/save-my-astra/zip/refs/heads/main').read()
unpack(data, root / 'source')
print('source ZIP SHA256:', hashlib.sha256(data).hexdigest())
if sys.version_info[:2] == (3, 12) and sys.platform == 'win32':
    metadata = json.load(urllib.request.urlopen('https://pypi.org/pypi/PyYAML/6.0.3/json'))
    item = next(x for x in metadata['urls'] if 'cp312-cp312-win_amd64.whl' in x['filename'])
    wheel = urllib.request.urlopen(item['url']).read()
    assert hashlib.sha256(wheel).hexdigest() == item['digests']['sha256']
    unpack(wheel, root / 'python-deps')
else:
    print('Install compatible PyYAML separately: python -m pip install PyYAML==6.0.3')
print('Prepared; next run python manage_install.py test test-home')

