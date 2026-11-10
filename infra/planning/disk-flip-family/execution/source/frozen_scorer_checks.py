from pathlib import Path
import sys,importlib.util,unittest,hashlib,json,datetime
root=Path(__file__).resolve().parents[1];snapshot=root/'df_family/snapshots/original-expert-v2'
sys.path.insert(0,str(snapshot));source=root/'tests/test_tabletop_disk_flip.py'
spec=importlib.util.spec_from_file_location('frozen_disk_checks',source);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
import humanoid.g1_tabletop_disk_flip.task_spec as task
assert Path(task.__file__).resolve().is_relative_to(snapshot)
class Results(unittest.TextTestResult):
 def __init__(self,*args,**kwargs):super().__init__(*args,**kwargs);self.passed=[]
 def addSuccess(self,test):super().addSuccess(test);self.passed.append(test.id())
result=unittest.TextTestRunner(verbosity=2,resultclass=Results).run(unittest.defaultTestLoader.loadTestsFromModule(module))
report=dict(schema='disk-flip-frozen-scorer-checks/1',created_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),snapshot='original-expert-v2',scorer_sha256=hashlib.sha256(Path(task.__file__).read_bytes()).hexdigest(),test_source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),tests_run=result.testsRun,passed=result.wasSuccessful(),passed_cases=result.passed,failures=[dict(test=str(t),message=e) for t,e in result.failures+result.errors],scope='Synthetic measurement/scorer and geometry regression checks against frozen sources. These do not constitute physical executions, isolated execution, human review, or second-person reproduction.')
out=root/'df_family/acceptance/original-frozen-scorer-checks.json';out.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(passed=report['passed'],tests_run=report['tests_run'],source=str(task.__file__))))
raise SystemExit(not result.wasSuccessful())
