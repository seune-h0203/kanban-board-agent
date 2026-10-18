"""Real localhost CLI->API->SQLite workflow smoke test, independent subprocesses."""
import json
import os
import pathlib
import subprocess
import sys
import socket
import tempfile
import time
import urllib.request

root=pathlib.Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory(prefix='kanban7-final-') as tmp:
    with socket.socket() as listener:
        listener.bind(('127.0.0.1', 0))
        port=listener.getsockname()[1]
    env=os.environ.copy()
    env.update({'DATABASE_URL':f'sqlite:///{tmp}/smoke.sqlite3','TEAM_TODO_API_KEY':'local-demo-only','KANBAN_API_URL':f'http://127.0.0.1:{port}'})
    seed=json.loads(subprocess.check_output([sys.executable,'-m','app.bootstrap'],cwd=root,env=env,text=True))
    env['TEAM_TODO_ACTOR_ID']=seed['actor_id']
    logfile=pathlib.Path(tmp)/'server.log'
    with logfile.open('w') as file:
        server=subprocess.Popen([sys.executable,'-m','uvicorn','app.main:app','--host','127.0.0.1','--port',str(port)],cwd=root,env=env,stdout=file,stderr=subprocess.STDOUT)
        try:
            for _ in range(70):
                try:
                    with urllib.request.urlopen(f'http://127.0.0.1:{port}/health',timeout=1) as request:
                        if request.status==200:break
                except Exception:time.sleep(.1)
            else:raise RuntimeError('server did not start')
            def cli(*args):
                result=subprocess.run([sys.executable,'-m','app.cli','--json',*args],cwd=root,env=env,capture_output=True,text=True,timeout=15)
                if result.returncode:raise RuntimeError((args,result.stdout,result.stderr))
                return json.loads(result.stdout)
            board, todo, doing, done = (seed[x] for x in ('board_id','todo_id','doing_id','done_id'))
            cmd=['kanban','register',board,'--work-key','assignment7/smoke-final','--title','CLI API DB Skill workflow']
            created=cli(*cmd,'--column-id',todo)
            c_id=created['id']
            planned=cli('kanban','log',c_id,'--kind','plan','--message','Smoke: verify actual server and DB')
            moving=cli(*cmd,'--column-id',doing)
            progress=cli('kanban','log',c_id,'--kind','progress','--message','Executed Typer against running FastAPI')
            result=cli('kanban','log',c_id,'--kind','result','--message','Smoke CLI HTTP test passed')
            done_card=cli(*cmd,'--column-id',done)
            saved=cli('kanban','get',c_id)
            assert all(x['id']==c_id for x in (created,moving,done_card,saved))
            assert saved['column_id']==done and saved['description'].count('[plan]')==1 and saved['description'].count('[progress]')==1 and saved['description'].count('[result]')==1
            assert 'Smoke CLI HTTP test passed' in saved['description']
            board_cards=cli('kanban','list',board)['items']
            assert len(board_cards)==1 and board_cards[0]['id']==c_id
            report={'outcome':'PASS','test':'localhost Typer CLI -> running FastAPI -> SQLite persistent DB','card_id':c_id,'board_id':board,'original_column_id':todo,'final_column_id':done,'activities':['plan','progress','result'],'list_card_count':len(board_cards),'original_database':'isolated temporary SQLite only','supabase_write':'not attempted','real_codex_session':'not executed'}
            (root/'docs'/'SMOKE_RESULT.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
            print(json.dumps(report,ensure_ascii=False,indent=2))
        finally:
            server.terminate()
            try:server.wait(timeout=5)
            except subprocess.TimeoutExpired:server.kill()
