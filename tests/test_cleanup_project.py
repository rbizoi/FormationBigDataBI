import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace

spec=importlib.util.spec_from_file_location('cleanup',Path(__file__).parents[1]/'tools/cleanup_project.py')
module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)


def test_cleanup_preview_is_project_scoped_and_does_not_delete(monkeypatch):
    calls=[]
    def fake(*args, **kwargs):
        calls.append(args)
        if 'config' in args:
            return json.dumps({'name':'formation-test','services':{'trino':{'image':'trinodb/trino:483'}}})
        return ''
    monkeypatch.setattr(module,'docker',fake)
    monkeypatch.setattr(module,'argparse',SimpleNamespace(ArgumentParser=lambda **kw:SimpleNamespace(add_argument=lambda *a,**kw:None,parse_args=lambda:SimpleNamespace(execute=False))))
    assert module.main()==0
    assert all('down' not in args and 'rm' not in args for args in calls)
    assert ('ps','-aq','--filter','label=com.docker.compose.project=formation-test') in calls
    assert ('volume','ls','-q','--filter','label=com.docker.compose.project=formation-test') in calls
