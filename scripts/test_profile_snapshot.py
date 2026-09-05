"""Offline check: pagination, escaping, language totals and last-good preservation."""
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import xml.etree.ElementTree as ET
import update_profile_snapshot as profile

repos = [dict(name=p[0], fork=False, archived=False, stargazers_count=2, pushed_at='2026-09-05T00:00:00Z') for p in profile.PROJECTS]
repos += [dict(name=f'extra-{i}', fork=False, archived=False, stargazers_count=0, pushed_at='2026-09-05T00:00:00Z') for i in range(95)]
calls = []
def fake_api(path, payload=None):
    calls.append(path)
    if '/users/' in path: return repos[:100] if path.endswith('page=1') else repos[100:]
    if '/releases?' in path: return [dict(tag_name='v1<&', draft=False, prerelease=False)]
    if path.endswith('/languages'): return {'Python': 70, 'Rust': 30}
    if '/search/issues?' in path: return {'total_count': 7}
    if path == '/graphql': return {'data': {'user': {'contributionsCollection': {'contributionCalendar': {'totalContributions': 123}}}}}
    raise AssertionError(path)

with TemporaryDirectory() as directory, patch.object(profile, 'OUT', Path(directory)), patch.object(profile, 'api', fake_api):
    profile.main()
    outputs = {p.name: p.read_bytes() for p in Path(directory).glob('*.svg')}
    assert len(outputs) == 7 and any(p.endswith('page=2') for p in calls)
    for content in outputs.values(): ET.fromstring(content)
    assert b'70.0%' in outputs['github-snapshot.svg']
    assert b'v1&lt;&amp;' in outputs['project-vibevoice.svg']
    with patch.object(profile, 'api', side_effect=OSError('offline')):
        try: profile.main()
        except OSError: pass
        else: raise AssertionError('Network failure must fail the refresh')
    assert outputs == {p.name: p.read_bytes() for p in Path(directory).glob('*.svg')}
print('Profile checks passed: pagination, escaping, totals and last-good preservation.')
