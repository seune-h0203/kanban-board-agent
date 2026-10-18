# TSD_CLI — 기술 설계

Entrypoint: `python -m app.cli`, 패키지 엔트리 `kanban7`. `--json`, `--text`, `--url`, `--actor-id`, `--api-key`는 공통 옵션이며 하위 명령 앞에 놓는다. HTTP 호출은 httpx를 사용하고 외부 DB를 직접 조작하지 않는다. 팀용 식별자는 UUID로 조회 후 사용. 토큰은 커맨드 기록 노출을 피하도록 환경변수를 권장한다. 실제 CLI 코드와 명령 목록은 `app/cli.py`, `app/kanban/cli.py`, `README.md`가 기준이다.
