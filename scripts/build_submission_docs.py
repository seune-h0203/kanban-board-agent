from pathlib import Path
p=Path(__file__).resolve().parents[1]
d=p/'docs'
d.mkdir(exist_ok=True)
docs={
'PRD.md':'''# PRD — 과제 #7 팀 공유 Kanban Agent

## 목표와 사용자
과제 #5에서 만든 6개 관계형 테이블을 변경하지 않고, 소규모 팀원과 Codex가 동일한 보드에 작업을 저장하도록 한다. 사용자: 보드 owner/editor/viewer 및 로컬 Codex 에이전트.

## 기능 요구사항
- FR1: 사용자는 소속 보드 및 멤버, 컬럼, 카드를 조회한다.
- FR2: 편집 권한이 있는 사용자는 카드를 생성, 수정, 이동, 삭제하고 담당자를 배정한다.
- FR3: CLI는 모든 공개 FastAPI 엔드포인트를 지원하며 사람이 읽는 text/에이전트용 JSON을 출력한다.
- FR4: Codex는 안정된 work-key로 중복 없이 작업을 등록하고 plan, progress, result, blocked 기록을 남긴다.
- FR5: 사용자는 동일 카드의 등록/변경 결과를 다시 조회하여 영속성을 검증한다.

## 완료 기준
12개 OpenAPI 작업과 CLI 매핑, 로컬 API/CLI/E2E 테스트 통과. 공유 Supabase 및 실제 Codex 시연은 별도로 검증하며 로컬 통과만으로 완료 처리하지 않는다.

## 범위 외
새 프런트엔드, 별도 로그인 서비스, 실시간 동기화, 기존 Supabase 스키마 자동 마이그레이션.
''',
'TSD.md':'''# TSD — 구조와 구현 판단

## 아키텍처
사용자/Codex → Typer CLI (HTTP) → FastAPI (SQLAlchemy) → 기존 PostgreSQL(Supabase) 또는 개발용 SQLite. Swagger: `/docs`, OpenAPI: `/openapi.json`.

## 데이터 일관성
board_members의 owner/editor는 쓰기 가능, viewer는 조회만 가능. 카드의 `column_id`가 상태를 나타낸다. 카드 할당자는 같은 보드의 구성원만 가능하며 잘못된 cross-board 업데이트를 차단한다. `register`는 보드+작성자+work-key 조합을 이용해 중복 생성을 줄인다. 기존 카드 설명에 로그를 누적하므로 길이 제한과 수정 가능성이 있다.

## 환경
Python 3.11–3.13, FastAPI, SQLAlchemy, Typer, httpx, pytest. 크로스플랫폼 실행: `python -m app.cli`. `TEAM_TODO_API_KEY`는 서버에서 필수(격리 로컬 시연 예외). PostgreSQL은 실제 스키마 검증 전 DDL 금지. 인터넷 공개 전에 JWT 기반 신원 확인 필요.

## 로컬 실행
`python -m pip install -e '.[dev]'`; `python -m app.bootstrap`; `python -m uvicorn app.main:app --host 127.0.0.1 --port 8000`; `python -m pytest -q`; `python scripts/smoke_local.py`.
''',
'DATABASE.md':'''# DATABASE — 기존 과제 #5 구조 유지

| 테이블 | 목적 | 주요 키와 제약 |
|---|---|---|
| users | 구성원 | id PK, email UNIQUE |
| boards | 보드 | id PK, owner_id → users |
| board_members | 협업 권한 | (board_id,user_id) 복합 PK, role |
| columns | 보드의 상태 | id PK, board_id FK, position |
| cards | 작업 | id PK, column_id FK, created_by FK, position |
| card_assignees | 다중 담당자 | (card_id,user_id) 복합 PK |

흐름: boards → columns → cards, users ↔ boards (board_members), users ↔ cards (card_assignees).

**주의**: 이는 업로드된 `kanban.zip`의 SQLAlchemy 스키마이며 실제 공유 Supabase 구조 일치 여부는 확인되지 않았다. DB가 비활성화된 상태에서는 테이블 생성·삭제·수정을 수행하지 않는다. 실제 연결 전 `python -m app.kanban.inspect_database`로 테이블, 타입, FK, RLS를 확인한다.
''',
'TEST_CASE.md':'''# TEST_CASE — API 및 DB 수용 기준

체크 항목은 로컬 격리 SQLite에서 자동 테스트로 확인했으며 라이브 Supabase 확인과 구별한다.

| 케이스 | Endpoint | Request | Expected response |
|---|---|---|---|
| TC-01 | GET /health | GET | 200, status |
| TC-02 | GET /api/v1/boards | actor/key 헤더 | 200, 접근 가능한 보드 |
| TC-03 | GET /api/v1/boards/{id}/columns | 소속 보드 ID | 200, 컬럼 배열 |
| TC-04 | POST /api/v1/boards/{id}/cards | title,column_id | 성공 시 카드 ID 반환 |
| TC-05 | GET /api/v1/cards/{id} | 생성된 ID | 200, 같은 카드 |
| TC-06 | PATCH /api/v1/cards/{id} | title/column_id | 200, 변경 내용 |
| TC-07 | POST /api/v1/cards/{id}/activities | kind,message | 200, 로그 누적 |
| TC-08 | DELETE /api/v1/cards/{id} | 생성된 ID | 성공 후 GET 404 |
| TC-09 | 쓰기 엔드포인트 | viewer actor | 403 |
| TC-10 | 쓰기 엔드포인트 | 다른 보드의 column/assignee | 422 또는 권한 오류 |
| TC-11 | 쓰기 엔드포인트 | 필수값 누락·공백·날짜 오류 | 422 |
| TC-12 | 쓰기 엔드포인트 | 키 누락/오류 | 401 또는 503 |

원문 테스트 코드: `tests/test_api.py`, `tests/test_database.py`, `tests/test_activity.py`. 실행: `python -m pytest -q`.
''',
'PRD_CLI.md':'''# PRD_CLI — Typer 명령 인터페이스

CLI는 비개발자도 명령과 `--help`만 보고 카드 작업을 수행하도록 한다. macOS, Linux, Windows의 Python 지원, 비대화형 명령, JSON 및 text 출력, 실패 시 0이 아닌 종료 코드가 요구된다. 모든 HTTP 엔드포인트와 CLI의 1:1 또는 동등 기능 매핑을 `README.md`에서 유지한다. Codex는 JSON을 우선 사용한다.
''',
'TSD_CLI.md':'''# TSD_CLI — 기술 설계

Entrypoint: `python -m app.cli`, 패키지 엔트리 `kanban7`. `--json`, `--text`, `--url`, `--actor-id`, `--api-key`는 공통 옵션이며 하위 명령 앞에 놓는다. HTTP 호출은 httpx를 사용하고 외부 DB를 직접 조작하지 않는다. 팀용 식별자는 UUID로 조회 후 사용. 토큰은 커맨드 기록 노출을 피하도록 환경변수를 권장한다. 실제 CLI 코드와 명령 목록은 `app/cli.py`, `app/kanban/cli.py`, `README.md`가 기준이다.
''',
'TEST_CASE_CLI.md':'''# TEST_CASE_CLI — CLI/E2E

| CLI 실행 | 검증 결과 |
|---|---|
| `python -m app.cli --help` | 일반 사용자가 볼 수 있는 명령 도움말 |
| `python -m app.cli --json health` | 유효한 JSON 및 성공 종료 코드 |
| `... --json kanban boards` | 보드 조회와 JSON 목록 |
| `... --json kanban register ... --work-key ...` 2회 | 같은 카드 ID, 카드 중복 없음 |
| `... --json kanban log ... --kind plan` | 단계별 로그 저장 |
| `... --json kanban get ...` | 업데이트된 내용 영속 조회 |
| 인증 키 누락 또는 URL 연결 실패 | 실패 종료/오류 안내 |

`tests/test_cli.py`와 `scripts/smoke_local.py`로 검증. 라이브 Supabase 및 실제 Codex 세션 결과는 별도 수동 시연 필요.
''',
'SECURITY_AUDIT.md':'''# 보안 감사 — 구현과 남은 위험

- 구현 확인: 보드 membership/role 검사, 잘못된 교차 보드 참조 거부, SQLAlchemy 바인딩, 기본 API 키 설정 필수, `.env` 및 SQLite 실행 데이터 제외.
- **중요 위험**: `X-Actor-ID` 헤더와 공유 API 키만으로 실제 사람 신원을 검증하지 못한다. 신뢰할 수 있는 로컬 시연 이외에는 공개 배포 금지. JWT 인증과 클레임→사용자 매핑 및 RLS 검증 필요.
- Supabase의 anon 키/사용자 JWT와 service_role/DB 관리자 자격증명을 혼동하면 안 된다. 서비스 비밀키를 CLI나 GitHub에 커밋하지 않는다.
- 누적 활동 로그는 `cards.description` 내 평문으로, 권한 있는 일반 수정으로 변경 가능하므로 법적/감사급 불변 이력이 아니다.
- 라이브 프로젝트 스키마/RLS/권한 미검증. 보안 감사 완료로 주장하지 않는다.
''',
'PERFORMANCE_AUDIT.md':'''# 성능 감사 — 범위와 제한

- 자동 테스트: 24개 API/CLI/SQLite 검사 통과. 별도 FastAPI 프로세스 + CLI 프로세스 로컬 E2E 통과.
- 라이브 PostgreSQL의 connection pool, 동시 사용자, 락 경합, 장기 부하 테스트 **미실시**. DB 프로젝트 비활성화 및 접근 제한으로 수행 불가.
- PostgreSQL row-level lock 및 카드 위치 유일성 제약은 실제 스키마/격리수준에 따라 추가 확인 필요.
- 실행 제안: 활성화된 테스트 DB와 분리된 테스트 보드를 확보한 뒤 10/50/100 동시 요청, p50/p95, 오류율, pool checkout wait, deadlock/timeout을 측정하여 결과를 여기에 첨부.
''',
'GITHUB_SUBMISSION.md':'''# GitHub 제출 상태

목표 저장소: https://github.com/seune-h0203/kanban-board-agent

현재 실행 컨테이너에서 github.com DNS 연결이 불가하여 `git push`를 실행하지 못했다. **로컬 ZIP 산출물을 업로드했다고 주장하지 않는다.** 연결 환경에서 GitHub로 올린 다음 저장소 파일 목록, 실제 commit SHA, GitHub Actions 성공 여부를 반드시 확인해야 한다.

## GitHub 업로드 예시

```bash
git init
git branch -M main
git add .
git commit -m "feat: complete assignment 7 kanban CLI and skill"
git remote add origin https://github.com/seune-h0203/kanban-board-agent.git
git push -u origin main
```

업로드 전 `.env`, DB URL, 토큰, 인증 키, 로컬 SQLite 파일을 반드시 재검사한다.
'''
}
for name,body in docs.items(): (d/name).write_text(body,encoding='utf-8')
(p/'AGENTS.md').write_text('''# Codex project instructions\n\n- Preserve the original `kanban/` sources; implement changes in `app/`.\n- Before changing code, review docs/PRD.md, TSD.md and TEST_CASE.md.\n- Use the local `kanban-task-tracker` skill to register work, plan, progress, results and blockers when a configured board is available. Never claim remote DB registration without reading it back.\n- After changes run `python -m pytest -q`, `python scripts/smoke_local.py`, and `ruff check .` if installed.\n- Never auto-migrate real Supabase tables or expose secrets.\n''',encoding='utf-8')
(p/'.github/workflows').mkdir(parents=True,exist_ok=True)
(p/'.github/workflows/ci.yml').write_text('''name: Python CI\non:\n  push:\n  pull_request:\njobs:\n  tests:\n    runs-on: ubuntu-latest\n    steps:\n      - uses: actions/checkout@v4\n      - uses: actions/setup-python@v5\n        with:\n          python-version: '3.12'\n      - run: python -m pip install -e '.[dev]'\n      - run: python -m ruff check app tests scripts\n      - run: python -m pytest -q\n      - run: python scripts/smoke_local.py\n''',encoding='utf-8')
print('Created',len(docs),'docs + AGENTS + CI')
