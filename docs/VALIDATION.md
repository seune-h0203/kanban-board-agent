# 과제 #7 실제 검증 보고서

**검증일:** 2026-10-18 (Asia/Seoul)  
**검증 환경:** Python 3.13.5, FastAPI 0.128.2, SQLAlchemy 2.0.50, Pydantic 2.13.5, Typer 0.26.3, pytest 9.0.2.  
**절차:** 코드 보존 확인 → SQLite 데이터베이스 생성·조회 → TestClient/CLI 통합 테스트 → 127.0.0.1 실제 HTTP 프로세스 호출 → Supabase 연결 메타데이터/읽기 전용 조회 시도. 이번 최종본은 작업 로그 누적 API와 CLI까지 보완 후 재테스트.

## 완료(재현된 결과)

| 항목 | 실제 수행 | 결과 |
|---|---|---|
| 소스 보존 | `kanban.zip`의 Python 파일 10개를 `kanban/`에 보존, `app/kanban/`에 작동 사본 복제 | **보존** |
| 서버 로딩 | `uvicorn app.main:app` 127.0.0.1:18765 실행, `/health` 요청 | **200 OK** (`database: not_checked`) |
| API 기능 | 사용자/보드/회원/컬럼/카드 조회, 생성/수정/이동/삭제 | **통과** (로컬 SQLite) |
| 역할 검사 | viewer 쓰기 거부, editor 쓰기 허용, 보드 외 UUID/담당자 입력 거부 | **403/422 확인** |
| 인증 설정 | 키 누락 401, 서버 키 미설정 503 | **통과** |
| 입력 검증 | 빈 PATCH, 공백 제목, timezone 없는 날짜, null 필수 값 | **422 확인** |
| 데이터 무결성 | 실제 SQLite 테이블 6개, FK 검증, 카드/담당자 영속화, 삭제 확인 | **통과** |
| CLI 실행 | `python -m app.cli`, 설치된 `kanban7`, 텍스트/JSON 출력 | **통과** |
| CLI 전체 API 매핑 | `/health`, 원래 Kanban API, 신규 활동기록 API에 Typer 명령 대응 | **매핑 확인** |
| 실제 CLI→HTTP→DB | 별도 실서버, 다른 프로세스의 CLI로 카드 등록→계획→진행→결과→완료→조회, 카드 ID 동일·카드 1개 확인 | **통과**, `docs/SMOKE_RESULT.json` |
| 작업 활동 기록 | 계획/진행/결과를 시간·작성자와 함께 기존 `cards.description`에 누적, viewer 거부·길이 초과 거부 | **통과** (로컬 SQLite) |
| Codex 중복 방지 | 동일 board+actor+work-key로 `register` 2회 실행 | **같은 카드 UUID 재사용**, 상태 컬럼 업데이트 |
| Codex Skill | skill-creator 초기화 도구로 생성, `package_skill.py` 검증·패키징 | **유효, `skill.zip` 생성** |
| 앱 설치 | `pip install -e . --no-deps --no-build-isolation`, `kanban7 --help` | **성공** (미설치 외부 의존성은 테스트 환경 기존 설치 활용) |
| 자동 테스트 | `pytest -q` | **24 passed** |
| 코드 컴파일 | `python -m compileall -q app` | **성공** |

**SQLite 스키마 점검:** `DATABASE_URL=sqlite:///./kanban-demo.sqlite3 python -m app.kanban.inspect_database` 결과 `required_columns_present: true`, `missing: []`, 테이블 6개, 보드 1개·사용자 3개·컬럼 3개. 이 결과에는 `integration_ready: false`가 명시된다. 이 도구는 읽기 전용 검사이며 원격 서버 연결과 동치가 아니다.

**실제 HTTP 시연 결과 예:** `register`로 카드 `f5036e99-d246-5e1b-b91e-b74e815734c1` 등록, 동일 work-key로 다른 컬럼으로 이동, `list`에 정확히 카드 1개 유지. **이 UUID는 로컬 시연 데이터의 것**이다.

## 미완료 / 검증 실패(절대 완료로 보고하지 않음)

| 항목 | 증거·상태 | 후속 조치 |
|---|---|---|
| **공유 Supabase 실제 테이블 검사** | 연결된 `gcs-database-class` 프로젝트는 `INACTIVE` 상태이며 read-only SQL 시도에서 `Connection terminated due to connection timeout` | 프로젝트 재개/권한 확인 후 스키마 읽기 재시도 |
| **다른 연결된 프로젝트 DB 검사** | 연결된 `cones's Project`에서 read-only SQL 연결에 `password authentication failed` (postgres/read-only user) | Supabase 인증 연결 수정/권한 확인 필요 |
| **원격 DB 실제 쓰기** | 미실행. 기존 데이터 변형 위험과 현재 DB 접근 실패 때문에 의도적으로 건드리지 않음 | DB 스키마·RLS/권한을 먼저 검증한 뒤 별도 테스트 보드에서만 진행 |
| **PostgreSQL CRUD 트랜잭션/락** | 로컬 SQLite에서만 실행. 실제 PostgreSQL의 데드락/동시성/트랜잭션 검증은 미수행 | 접근 복구 후 제한적 통합 테스트 필요 |
| **Codex 사용자 실계정 저장** | 스킬 파일 생성/검증 및 CLI 등록 절차 구현. Codex 에이전트가 실제 공유 보드에 기록한 결과는 없음 | 올바른 계정·보드 ID로 시연 필요 |
| **원본 전체 프런트엔드와 호환성** | 이전에 공유된 `kanban.zip`에는 `kanban/` Python 코드만 포함됨. 프런트엔드 및 원격 GitHub 저장소는 이번 산출물 소스에 없음 | 실제 프런트 API 계약과 매핑 점검 필요 |
| **운영 인증 보안** | `X-Actor-ID`와 공유 키 기반의 신뢰된 개발 환경 접근 제어만 검증, 사람별 서명 JWT 검증은 아직 없음 | 인터넷 공개 전 JWT 유효성·주체/역할 매핑 구현 |
| **공유 Supabase 스키마 일치** | 원본 발표 파일의 `user_id`, `owner_user_id`, `title` 등 일부 표현과 현재 모델의 `id`, `owner_id`, `name`이 다름 | 실제 컬럼명/타입/FK 제약을 기준으로 **확인 후** 매핑 조정 |

## 원본 변경 내역(임의 삭제 없음)

- 보존: 원본 `kanban/` Python 소스 10개와 생성 당시 `__pycache__`(최종 제출 ZIP에서는 실행 캐시 제외).
- 적용 사본: `app/kanban/`에 10개 Python 파일. `api.py`: 서버 키 미설정 시 보안상 거부. `cli.py`: DELETE JSON 출력. `shared_cli.py`: Supabase 사용자 JWT 요구. `tracking.py`: 빈 work-key 방지, 등록 저장 후 보드·작성자도 검증.
- 신규: `app/db/`, `app/main.py`, `app/cli.py`, `app/bootstrap.py`, `tests/`, `.agents/skills/`, 프로젝트 설정 및 문서.
- 공유 DB 작업: **DDL / 마이그레이션 / 데이터 생성·삭제 전혀 실행하지 않음.**

## 환경 분리·안전

실제 검증에서 사용한 `kanban-demo.sqlite3`는 별도 시연 데이터베이스이다. 제출 ZIP에는 실 DB URL, 비밀 키, `.env`, `*.sqlite3`, 테스트 캐시를 포함하지 않는다. `python -m app.bootstrap`는 외부 Postgres를 거부하며 **SQLite에만 샘플**을 만든다. 외부 공개 API에는 공유 키 방식이 충분한 인증이 아니므로 수업 시연에서는 `127.0.0.1` 바인딩을 유지한다.


## 추가 구현(레퍼런스의 방향성만 적용)

- `POST /api/v1/cards/{id}/activities` 및 `kanban log` 신규 구현: 기존 `cards.description`에 로그를 **원자적으로 추가**(Postgres는 보드 row locking; SQLite는 BEGIN IMMEDIATE). 생성 시 시간·실제 actor UUID·단계(plan/progress/result/blocked)를 포함한다.
- 기존 테이블 여섯 개는 변경하지 않았고 기존 11개 엔드포인트(`/health` 포함)를 삭제하지 않았다. 활동 API 추가 후 12개 엔드포인트가 되었다.
- 실패/차단된 Codex 작업은 `blocked`로 기록하고 Done으로 옮기지 않게 Skill을 강화했다.
- 한계: 장기적인 활동 이력은 기존 description 5,000자에 제한된다. 역할 권한이 있는 사용자가 일반 PATCH를 이용해 내용을 수정하는 기능도 그대로 있으므로 이것은 변조 방지 감사 로그는 아니다.

### 최종 재검증

- 추가 테스트 `tests/test_activity.py` 3개 실행(활동 기록 순서/SQLite 영속화, viewer/유효성/가득 찬 로그 거부, JSON·텍스트 CLI).
- `python -m pytest -q`: **24 passed**. 이 실행은 로컬 SQLite에 한정되며 Codex 자체 사용이나 원격 Supabase 쓰기 테스트를 대체하지 않는다.
- `gcs-database-class` 상태 재확인: 2026-10-18 **INACTIVE**. Supabase `list_tables` 읽기 요청 역시 `Connection terminated due to connection timeout`; 따라서 실제 공유 Supabase의 스키마/RLS 검증은 아직 불가.

### 로컬 실제 HTTP 독립 시연 (2026-10-18 최종 재실행)

`scripts/smoke_local.py`는 격리된 임시 SQLite 생성, FastAPI 프로세스 실행, Typer CLI 프로세스에서 등록 및 계획/진행/결과 로그 작성, 최종 조회와 카드 중복 미발생까지 확인한다. **PASS**, 결과는 `docs/SMOKE_RESULT.json`에 있다. 테스트 자체는 Codex 에이전트가 실행했다는 의미가 아니라 **Codex Skill에 정의된 CLI 절차를 독립 프로세스로 실행 가능하다는 검증**이다.

이번 실행에서는 `ruff`가 설치되어 있지 않아 lint 검증은 실행하지 못했다(로컬 실행 `No module named ruff`). CI에서 `pip install -e '.[dev]'` 설치 후 `ruff check .` 실행을 권장한다.
