"""Wait for the existing frozen process, then verify and publish its artifacts.

No target solver, restart, runtime cutoff, or numerical parameter mutation.
"""
import argparse
from datetime import datetime, timezone
import fcntl
from importlib.metadata import version
import json
import os
from pathlib import Path
import subprocess
import time

import vacuum_registered_run as registered

ROOT=registered.ROOT
D=registered.D
MANIFEST=D/'completion-monitor.json'
RUNTIME=Path('/tmp/quod-vacuum-completion-monitor')
REGISTRATION_COMMIT='4cbbe83cb8689a722f3bf20c92376725a7fefa55'
SOURCES=('scripts/vacuum_completion_monitor.py','scripts/test_vacuum_completion_monitor.py',
         'scripts/vacuum_selected_report.py','scripts/test_vacuum_selected_report.py',
         'scripts/vacuum_single_report.py','scripts/test_vacuum_single_report.py')


def commands():
    return [['python3','scripts/vacuum_registered_run.py','verify','--registration-commit',REGISTRATION_COMMIT],
            ['python3','scripts/vacuum_selected_report.py'],
            ['python3','scripts/vacuum_single_report.py'],
            ['python3','-m','unittest','discover','-s','scripts','-p','test_vacuum*.py']]


def publication_context():
    """Bind publication to one attached branch and one explicit origin endpoint."""
    def output(*args):
        return subprocess.check_output(['git',*args],cwd=ROOT).decode().strip()
    try:
        branch=output('symbolic-ref','--quiet','--short','HEAD')
        upstream=output('rev-parse','--abbrev-ref','--symbolic-full-name','@{upstream}')
    except subprocess.CalledProcessError as exc:
        raise ValueError('publication requires an attached branch with an upstream') from exc
    urls=output('remote','get-url','--all','origin').splitlines()
    push_urls=output('remote','get-url','--push','--all','origin').splitlines()
    if not branch or upstream!='origin/'+branch or len(urls)!=1 or len(push_urls)!=1:
        raise ValueError('publication requires one origin endpoint and a matching origin branch upstream')
    return {'branch':branch,'origin_url':urls[0],'origin_push_url':push_urls[0],'upstream':upstream}


def manifest():
    return {'schema_version':1,'scope':__doc__,'registration_commit':REGISTRATION_COMMIT,
            'publication':publication_context(),
            'registration_sha256':registered.digest(registered.REGISTRATION.read_bytes()),
            'source_sha256':{p:registered.digest((ROOT/p).read_bytes()) for p in SOURCES},
            'report_dependencies':{p:version(p) for p in ('sympy','matplotlib')},
            'commands':commands(),'poll_seconds':30,
            'failures':'Preserve evidence; stop monitor on drift, unexpected process exit, failed verification/test/publication; never restart targets or silently retry finalization.'}


def validate(value,commit):
    if value!=manifest():raise ValueError('completion-monitor source/dependency/specification drift')
    registered.committed(json.loads(registered.REGISTRATION.read_text()),REGISTRATION_COMMIT)
    if len(commit)!=40 or any(c not in '0123456789abcdef' for c in commit):
        raise ValueError('full monitor commit required')
    def blob(path):return subprocess.check_output(['git','show',commit+':'+path],cwd=ROOT)
    if blob(str(MANIFEST.relative_to(ROOT)))!=MANIFEST.read_bytes():raise ValueError('monitor manifest not committed')
    for path,sha in value['source_sha256'].items():
        if registered.digest(blob(path))!=sha:raise ValueError('monitor source not committed: '+path)


def original_process_alive(pid):
    try:parts=Path(f'/proc/{pid}/cmdline').read_bytes().split(b'\0')
    except FileNotFoundError:return False
    expected=[b'scripts/vacuum_registered_run.py',b'run',b'--registration-commit',REGISTRATION_COMMIT.encode()]
    return parts[1:5]==expected and len(parts)==6 and parts[-1]==b''


def inspect(index,value):
    if index['registration_commit']!=REGISTRATION_COMMIT or index['registration_sha256']!=value['registration_sha256']:
        raise ValueError('run/monitor registration mismatch')
    expected=registered.core.baseline.target_ids()
    if [r['id'] for r in index['cells']]!=expected or index['selected']!=42:
        raise ValueError('run inventory mismatch')
    terminal=index['state'] in ('completed','completed_with_failures')
    if terminal and (index['attempted']!=42 or any(r['result'] is None or not r['attempted'] for r in index['cells'])):
        raise ValueError('incomplete run cannot trigger finalization')
    if index['state'] not in ('running','completed','completed_with_failures'):
        raise ValueError('run needs attention: '+index['state'])
    return terminal


def status(phase,**fields):
    registered.core.baseline.write_report(RUNTIME/'status.json',dict(
        phase=phase,observed_utc=datetime.now(timezone.utc).isoformat(),**fields))


def finalize(index,value,commit):
    validate(value,commit)
    if not inspect(index,value):raise ValueError('run not terminal')
    if subprocess.check_output(['git','diff','--cached','--name-only'],cwd=ROOT).strip():
        raise ValueError('existing staged changes; refusing to commit other work')
    subprocess.run(['git','diff','--exit-code','--','research/vacuum-spectrum/VACUUM-REPORT.html',
                    'research/vacuum-spectrum/AUTONOMOUS-STATUS.md'],cwd=ROOT,check=True)
    log=D/'selected-run/completion-validation.txt'
    for path in (log,D/'selected-summary.json',D/'selected-run/verification.json'):
        if path.exists():raise FileExistsError('refusing to overwrite prior finalization: '+str(path))
    env=dict(os.environ,OPENBLAS_NUM_THREADS='1',MPLCONFIGDIR='/tmp/vacuum-mpl')
    with log.open('x') as stream:
        for command in value['commands']:
            status('finalizing',command=command)
            stream.write('\nCOMMAND '+json.dumps(command)+'\n');stream.flush()
            subprocess.run(command,cwd=ROOT,env=env,stdout=stream,stderr=subprocess.STDOUT,check=True)
    validate(value,commit)
    verdict=json.loads((D/'selected-run/verification.json').read_text())
    if verdict['status']!='verified' or verdict['cells']!=42:raise ValueError('missing complete verification')
    (D/'AUTONOMOUS-STATUS.md').write_text(
        '# Registered finite-rotor execution completed\n\n'
        'All 42 selected cells were attempted under registration `'+REGISTRATION_COMMIT+'`.\n'
        'Complete evidence replay and the report regression suite passed. Outcomes: `'+json.dumps(verdict['outcomes'],sort_keys=True)+'`.\n\n'
        '`VACUUM-REPORT.html` contains final results and the next research decision.\n'
        '`selected-run/completion-validation.txt` retains verification and test output;\n'
        '`selected-run/index.json` retains every outcome and checkpoint reference.\n'
        'The earlier live snapshot remains a historical record. Independent review\n'
        'covers the 21 SU(2) cells; review of completed U(1) results remains pending.\n\n'
        'The original pilot is permanently unverifiable. Full gaps and observable\n'
        'thresholds remain distinct. No uniform Yang–Mills gap proof is claimed.\n')
    paths=[D/'VACUUM-REPORT.html',D/'AUTONOMOUS-STATUS.md',D/'selected-summary.json',log,
           D/'selected-run/index.json',D/'selected-run/verification.json']
    paths.extend(D/'selected-run'/r['path'] for r in index['checkpoints'])
    paths.extend(D/'selected-run'/r['result']['path'] for r in index['cells'])
    if subprocess.check_output(['git','diff','--cached','--name-only'],cwd=ROOT).strip():
        raise ValueError('staged changes appeared during finalization; refusing publication')
    if publication_context()!=value['publication']:raise ValueError('publication checkout or remote drift')
    relative_paths=[str(p.relative_to(ROOT)) for p in paths]
    subprocess.run(['git','add','--',*relative_paths],cwd=ROOT,check=True)
    subprocess.run(['git','commit','--only','-m','Verify all registered cells and publish final finite-rotor report','--',*relative_paths],cwd=ROOT,check=True)
    head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT).decode().strip()
    if publication_context()!=value['publication']:raise ValueError('publication checkout or remote drift')
    subprocess.run(['git','push','origin','HEAD:refs/heads/'+value['publication']['branch']],cwd=ROOT,check=True)
    status('completed_and_pushed',commit=head,verification=verdict)


def watch(pid,commit):
    RUNTIME.mkdir(parents=True,exist_ok=True)
    with (RUNTIME/'lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
        try:
            value=json.loads(MANIFEST.read_text());validate(value,commit)
            while True:
                if value!=manifest():raise ValueError('completion-monitor source/dependency/specification drift')
                index=json.loads((D/'selected-run/index.json').read_text())
                if inspect(index,value):
                    finalize(index,value,commit);return
                if not original_process_alive(pid):
                    raise RuntimeError('original process is no longer visible; preserve incomplete run and investigate')
                status('waiting_for_original_run',pid=pid,attempted=index['attempted'],
                       completed=sum(r['result'] is not None for r in index['cells']),
                       checkpoints=len(index['checkpoints']),registration_commit=REGISTRATION_COMMIT)
                time.sleep(value['poll_seconds'])
        except Exception as exc:
            status('needs_attention',reason=f'{type(exc).__name__}: {exc}')
            raise


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=('prepare','watch'))
    parser.add_argument('--pid',type=int)
    parser.add_argument('--monitor-commit')
    args=parser.parse_args()
    if args.action=='prepare':registered.core.baseline.write_report(MANIFEST,manifest())
    else:watch(args.pid,args.monitor_commit)
