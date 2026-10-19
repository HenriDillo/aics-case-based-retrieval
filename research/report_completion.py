"""Supplement the existing provisional run without altering results or methodology.

python -m research.report_completion --output research/generated/report-supplement-v1
"""
import argparse
import ctypes
import hashlib
import json
import platform
from pathlib import Path
from statistics import median
import subprocess
import sys
from time import perf_counter

from backend.study_loader import load_study_csv
from backend.study_retrieval import retrieve
from research.evaluate import PARTNERS
from research.validate_intake import validate

ROOT = Path(__file__).resolve().parents[1]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def working_set_bytes():
    if sys.platform != 'win32':
        return None
    class Counters(ctypes.Structure):
        _fields_ = [('cb',ctypes.c_ulong),('PageFaultCount',ctypes.c_ulong)] + [
            (name,ctypes.c_size_t) for name in ('PeakWorkingSetSize','WorkingSetSize',
            'QuotaPeakPagedPoolUsage','QuotaPagedPoolUsage','QuotaPeakNonPagedPoolUsage',
            'QuotaNonPagedPoolUsage','PagefileUsage','PeakPagefileUsage')]
    counters = Counters()
    counters.cb = ctypes.sizeof(counters)
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    kernel.GetCurrentProcess.restype = ctypes.c_void_p
    psapi = ctypes.WinDLL('psapi', use_last_error=True)
    psapi.GetProcessMemoryInfo.argtypes = [ctypes.c_void_p,ctypes.POINTER(Counters),ctypes.c_ulong]
    if not psapi.GetProcessMemoryInfo(kernel.GetCurrentProcess(),ctypes.byref(counters),counters.cb):
        raise ctypes.WinError(ctypes.get_last_error())
    return counters.WorkingSetSize


def environment():
    cmd = "[PSCustomObject]@{processor=(Get-CimInstance Win32_Processor | Select-Object -ExpandProperty Name); ram_bytes=(Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory; os=(Get-CimInstance Win32_OperatingSystem).Caption; os_version=(Get-CimInstance Win32_OperatingSystem).Version} | ConvertTo-Json"
    hardware = json.loads(subprocess.check_output(['powershell','-NoProfile','-Command',cmd],text=True))
    libraries = json.loads(subprocess.check_output([sys.executable,'-m','pip','list','--format=json'],text=True))
    lock = json.loads((ROOT/'frontend/package-lock.json').read_text())
    frontend = {key.removeprefix('node_modules/'):value['version'] for key,value in lock['packages'].items()
                if key in ('node_modules/react','node_modules/react-dom','node_modules/vite','node_modules/@vitejs/plugin-react')}
    remote = subprocess.check_output(['git','remote','get-url','origin'],cwd=ROOT,text=True).strip()
    return dict(hardware=hardware,python=platform.python_version(),libraries=libraries,
                frontend_versions=frontend,repository=remote,
                repository_privacy='Not verified with hosting provider; no push performed',
                requirements_lock_sha256=sha(ROOT/'backend/requirements-lock.txt'))


def report(output):
    output.mkdir(parents=True, exist_ok=False)
    def save(name,value):
        (output/name).write_text(json.dumps(value,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    gen=ROOT/'research/generated/v26'
    old=ROOT/'research/generated/evaluation-v1'
    hashes={p.name:sha(p) for p in old.iterdir() if p.is_file()}
    save('environment.json',environment())
    source=load_study_csv(ROOT/'backend/data/study_intake.csv')
    base=load_study_csv(gen/'case_base_p00.csv')
    judged=load_study_csv(gen/'judged_p00.csv')
    save('required-wage-validation.json',validate(source.records))
    save('missingness.json',dict(original_case_base=source.report,
                                 provisional_case_base=base.report,judged=judged.report))
    counts={}
    for split,queries in [('leave_one_applicant_out',base.records),('reviewed',judged.records)]:
        rows=json.loads((old/f'p00_{split}_events.json').read_text())
        assert len(queries) == len(rows), 'Saved evaluation query count differs'
        details=[]
        for query,row in zip(queries,rows):
            assert (query.applicant_id, query.event_id) == (row['applicant_id'], row['event_id'])
            result=retrieve(query,base.records,exclude_applicant_ids=row['excluded_applicants'])
            assert [[m.record.applicant_id,m.record.event_id] for m in result.matches] == row['neighbors']
            details.append(dict(applicant_id=query.applicant_id,event_id=query.event_id,
                assistance_type=query.values['assistance_type_granted'],undefined_pairs=result.undefined_pairs,
                neighbors=[dict(applicant_id=m.record.applicant_id,event_id=m.record.event_id,
                                compared_field_count=len(m.field_scores)) for m in result.matches]))
        for condition in ['p25','p50','p75']:
            other=json.loads((old/f'{condition}_{split}_events.json').read_text())
            assert len(rows) == len(other), 'Condition query counts differ'
            assert all(a['neighbors']==b['neighbors'] and a['numeric_ranges']==b['numeric_ranges']
                       and a['active_fields']==b['active_fields'] for a,b in zip(rows,other))
        counts[split]=details
        print(f'{split}: comparison counts recorded',flush=True)
    save('compared-field-counts.json',dict(applies_to=['p00','p25','p50','p75'],splits=counts))
    validations=json.loads((gen/'validation.json').read_text())
    comparisons={}
    for condition,validation in validations.items():
        comparisons[condition]={}
        for kind in ['case_base','judged']:
            comparisons[condition][kind]=[
                dict(row,comparison_target=row['rule_base'],
                     difference=(row['mean_amount']-row['rule_base']) if row['aggregate_share'] is None
                     else row['aggregate_share']-row['rule_base'])
                for row in validation[f'{kind}_summary']]
    save('benchmark-comparisons.json',dict(status='Provisional generated data; no realism validation claim',
        cost_checks=json.loads((gen/'cost_checks.json').read_text()),amount_and_share_comparisons=comparisons,
        note='Rule bases are rounded published shares or declared assumptions. Devices and transportation are assumptions, not Region XI benchmarks. Direct food/cash means are compared in pesos.'))
    # Retrieval timing for one fixed reviewed query from each type, not weight-search runtime.
    timing=[]
    for typ in sorted({r.values['assistance_type_granted'] for r in judged.records}):
        query=next(r for r in judged.records if r.values['assistance_type_granted']==typ)
        exclusions=[PARTNERS[query.applicant_id]] if query.applicant_id in PARTNERS else []
        for _ in range(3): retrieve(query,base.records,exclude_applicant_ids=exclusions)
        elapsed=[]
        for _ in range(11):
            start=perf_counter()
            retrieve(query,base.records,exclude_applicant_ids=exclusions)
            elapsed.append((perf_counter()-start)*1000)
        timing.append(dict(type=typ,query=query.applicant_id,median_ms=median(elapsed),runs_ms=elapsed))
    # A fresh process imports the actual backend app and loads its configured default CSV.
    memory_command='from backend.main import app; from backend.data_store import load_cases; from research.report_completion import working_set_bytes; load_cases(); print(working_set_bytes())'
    memory=[int(subprocess.check_output([sys.executable,'-c',memory_command],cwd=ROOT,text=True).strip()) for _ in range(5)]
    save('performance.json',dict(retrieval=timing,warmup_runs=3,timed_runs=11,
        backend_memory=dict(metric='Process working set after importing app and loading default CSV; not peak and not a running HTTP-server load test',
                            runs_bytes=memory,median_bytes=median(memory)),
        full_weight_evaluation_runtime=None,reason='Weight search not implemented or selected; cannot fabricate full runtime'))
    assert hashes=={p.name:sha(p) for p in old.iterdir() if p.is_file()}
    save('provenance.json',dict(original_evaluation_unchanged=True,evaluation_hashes=hashes,
        report_code_sha256=sha(Path(__file__)),status='Reporting supplement only; no methods selected'))


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    report(args.output)
