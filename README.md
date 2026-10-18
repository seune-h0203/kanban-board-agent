# 과제 #7 | 기존 Kanban Board → FastAPI + Typer CLI + Codex Skill

**범위:** 2026-10-18 작업본. 과제 #5의 6개 테이블을 대상으로 기존 `kanban.zip`의 기능을 실행 가능한 앱으로 연결했다. **공유 Supabase 실제 연결 성공을 의미하지 않는다.**

## 과제 요구와 구현 범위

| 요구 | 산출물 | 검증 상태 |
|---|---|---|
| 기존 소스 분석·보존 | `kanban/` 원본 10개 Python 소스 그대로 보존; `app/kanban/` 작동 사본 | 원본과 비교 가능 |
| 데이터 모델 | `app/kanban/models.py`: users, boards, board_members, columns, cards, card_assignees | 로컬 SQLite 관계형 DB 확인 |
| FastAPI 백엔드 | `app/main.py`, `app/kanban/api.py`, `app/db/` | 로컬 요청 검증 |
| 모든 API용 CLI | `app/cli.py`, `app/kanban/cli.py` | Typer 실제 동작 검증 |
| Codex Skill | `.agents/skills/kanban-task-tracker/SKILL.md` | 구조 검사, 등록 시나리오 확인 |
| API / CLI / DB 테스트 | `tests/`, `scripts/smoke_local.py` | 24개 테스트와 별도 실서버 로컬 통합 검증 |
| Supabase 실 DB | 연결된 프로젝트 두 개에 읽기 전용 조회 시도 | **연결 실패, 미완료** |

프로젝트의 루트 `kanban/` 폴더는 업로드된 압축파일의 원본을 보존한다. `app/kanban/`는 애플리케이션에서 import 가능하도록 사본을 둔 것으로, 기존 카드 CRUD/권한검사/업무등록 로직을 유지한다. 실행 보조 모듈을 새로 작성했으며 `app/kanban/api.py`는 기본 API 키 설정 없이는 요청을 거절하도록 강화했다. `app/kanban/cli.py`는 DELETE 시 JSON 성공 응답을 제공한다. `app/kanban/shared_cli.py`는 Supabase 사용자 JWT 설정을 요구한다. `app/kanban/tracking.py`는 빈 작업 키를 거부하고 등록 후 보드·작성자 확인을 추가한다. **기존 다른 프런트엔드 코드, 원격 저장소 전체는 압축파일에 없었으므로 전체 기존 서비스 호환성은 보증할 수 없다.**

## 1. 로컬 실행 (Windows / macOS / Linux)

Python 3.11–3.13 필요. 압축을 푼 폴더에서 다음을 실행한다.

```bash
python -m venv .venv
# 활성화(Windows PowerShell): .venv\Scripts\Activate.ps1
# 활성화(macOS/Linux): source .venv/bin/activate
python -m pip install -e '.[dev]'
python -m app.bootstrap
```

`python -m app.bootstrap`는 **SQLite에 한해서만** 별도 데모 DB와 샘플 users/board/columns를 만든다. Supabase/PostgreSQL에 대한 테이블 자동 생성·시딩은 없다. 부트스트랩 출력의 `actor_id`, `board_id`, `todo_id`, `doing_id`, `done_id`를 시연 명령에 넣는다.

**API 서버 (터미널 A)**

```bash
# macOS/Linux (이 예시는 터미널 프로세스 안에서만 적용)
export TEAM_TODO_API_KEY=change-me-for-demo
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Windows PowerShell:

```powershell
$env:TEAM_TODO_API_KEY = "change-me-for-demo"
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

접근: `http://127.0.0.1:8000/docs` (Swagger UI). `/health`는 프로세스 상태만 확인하고 DB 연동 완료를 의미하지 않는다. API 키가 없으면 기본적으로 API는 **503**을 반환한다. 키 없이 사용할 `KANBAN_ALLOW_INSECURE_DEMO=1`은 외부 공개가 없는 로컬 시연에서만 사용한다.

**CLI (터미널 B)** — 공통 전역 옵션은 하위 명령 `kanban`보다 **앞**에 쓴다.

```bash
python -m app.cli --actor-id <ACTOR_UUID> --api-key change-me-for-demo --json kanban boards
python -m app.cli --actor-id <ACTOR_UUID> --api-key change-me-for-demo --text kanban columns <BOARD_UUID>
python -m app.cli --actor-id <ACTOR_UUID> --api-key change-me-for-demo --json kanban create <BOARD_UUID> --column-id <TODO_UUID> --title "API 작성" --description "카드 CRUD"
python -m app.cli --actor-id <ACTOR_UUID> --api-key change-me-for-demo --json kanban list <BOARD_UUID>
```

명령마다 `--actor-id`, `--api-key`를 쓰기 싫으면 환경변수 `TEAM_TODO_ACTOR_ID`, `TEAM_TODO_API_KEY`를 설정한다. `--url` 또는 `KANBAN_API_URL`로 서버 URL을 변경할 수 있다. 운영 키는 실행 커맨드 옵션보다 **환경변수 사용 권장**(터미널 기록 노출 예방).

### 전체 API와 CLI 매핑

| HTTP | API 경로 | CLI 명령 (`python -m app.cli [공통옵션] ...`) |
|---|---|---|
| GET | `/health` | `health` |
| GET | `/api/v1/users` | `kanban users` |
| GET | `/api/v1/boards` | `kanban boards` |
| GET | `/api/v1/boards/{id}` | `kanban board BOARD_ID` |
| GET | `/api/v1/boards/{id}/members` | `kanban members BOARD_ID` |
| GET | `/api/v1/boards/{id}/columns` | `kanban columns BOARD_ID` |
| GET | `/api/v1/boards/{id}/cards` | `kanban list BOARD_ID [--column-id ... --assignee-id ... --limit ... --offset ...]` |
| POST | `/api/v1/boards/{id}/cards` | `kanban create BOARD_ID --column-id ... --title ... [--assignee-id ...]` |
| GET | `/api/v1/cards/{id}` | `kanban get CARD_ID` |
| PATCH | `/api/v1/cards/{id}` | `kanban update CARD_ID [--title ... --column-id ... --description ... --due-date ... --clear-assignees]` |
| POST | `/api/v1/cards/{id}/activities` | `kanban log CARD_ID --kind plan --message "계획"` |
| DELETE | `/api/v1/cards/{id}` | `kanban delete CARD_ID` |

`kanban log CARD_ID --kind plan|progress|result|blocked --message "..."`는 **기존 cards.description에 시간·작성자·단계를 남기는 append-only 기록 API**를 사용한다. 기존 설명을 지우지 않고 순서대로 누적한다(필드 5,000자 초과 시 409 반환). 별도 댓글 테이블은 생성하지 않으므로 과제 #5의 DB 구조를 임의 변경하지 않는다.

`kanban register BOARD_ID --column-id COLUMN_ID --work-key STABLE_NAME --title "..."`는 기존 POST+GET 또는 PATCH+GET을 조합한 **중복 방지형 업무 등록**이다. 같은 보드·작성자·work-key로 호출하면 기존 카드 ID를 재사용한다. 등록 이후 읽기 검증을 수행하므로 작업한 척하지 않는다. `--json`은 UTF-8 JSON 출력, 기본 `--text`는 사람이 읽을 수 있는 필드 출력. 삭제도 JSON 모드에서 `{"deleted": true}`를 출력한다.

## 2. Codex에서 실제 업무를 간반보드에 기록

Codex가 명령을 실제 실행할 수 있는 프로젝트 루트에서 `.agents/skills/kanban-task-tracker/SKILL.md`가 저장소 스킬로 탐색된다. 다음 명령처럼 요청하거나 스킬을 지정해 작업시킨다.

> `$kanban-task-tracker로 과제 #7 CLI 테스트를 작업 카드에 등록하고, 테스트가 완료되면 완료 컬럼으로 옮겨줘.`

**예시** (환경변수는 서버와 CLI 양쪽에서 준비되어야 함):

```bash
python -m app.cli --json kanban register <BOARD_UUID> --column-id <TODO_UUID> --work-key assignment7-cli-tests --title "CLI 통합 테스트" --description "테스트 진행 전"
python -m app.cli --json kanban log <CARD_UUID> --kind plan --message "CLI/API 통합 테스트 계획"
python -m app.cli --json kanban register <BOARD_UUID> --column-id <DOING_UUID> --work-key assignment7-cli-tests --title "CLI 통합 테스트"
python -m app.cli --json kanban log <CARD_UUID> --kind progress --message "수정 파일과 진행 상황"
# 테스트를 실제 실행하고 결과를 확인한 다음에만:
python -m app.cli --json kanban log <CARD_UUID> --kind result --message "테스트 실행 결과: 실제 검증 내역"
python -m app.cli --json kanban register <BOARD_UUID> --column-id <DONE_UUID> --work-key assignment7-cli-tests --title "CLI 통합 테스트"
```

성공 여부는 JSON에 `id`, `board_id`, `column_id`, `title`이 있는지 확인하고, `kanban get CARD_ID`로 다시 읽는다. 실제 사용자·보드·컬럼 ID를 조회한 뒤 기존 팀 보드에서 실행해야 하며, 데모 UUID를 실 DB에 적용하지 않는다.

## 3. Supabase 연동 (기존 DB 보존)

**DB 이름만으로 연동하지 않는다.** 압축파일 SQLAlchemy 모델의 테이블/컬럼은 다음과 같다.

- `users(id, email, name, created_at, updated_at)`
- `boards(id, owner_id, name, description, created_at, updated_at)`
- `board_members(board_id, user_id, role, joined_at)`
- `columns(id, board_id, name, position, created_at, updated_at)`
- `cards(id, column_id, title, description, position, due_date, created_by, created_at, updated_at)`
- `card_assignees(card_id, user_id, assigned_at)`

원본 과제 #5 PPT에서는 `user_id`, `owner_user_id`, `title` 같은 **다른 컬럼 이름도 등장하므로**, 현재 실제 프로젝트의 스키마를 확인하지 않고 연결하면 위험하다. 먼저 기존 Postgres DB에 **읽기 전용**으로 다음을 수행한다.

```bash
# DATABASE_URL은 Supabase 콘솔에서 받아온 기존 연결 문자열을 안전하게 설정한다.
python -m app.kanban.inspect_database
```

출력의 `required_columns_present`, 필드 타입, PK/FK, UNIQUE, RLS, 연결 계정 권한을 검증한다. 컬럼 유무 검사 결과가 참이어도 완전 호환이 보증되는 것은 아니다. 기본 모델은 기존 테이블에 맞춘 것으로, `alembic upgrade` 또는 `create_all()`을 Postgres에 실행하지 않는다. 확인된 DB URL을 앱 백엔드의 `DATABASE_URL`에만 설정한다. 백엔드가 직접 Postgres에 접속할 때는 적절한 별도 **최소권한 DB 계정**을 사용하고, HTTP 요청에는 별도 팀 인증/권한 계층이 필요하다.

`shared get/register`는 별도 Supabase Data API 보조 모드이다. `SUPABASE_URL`, `SUPABASE_PUBLISHABLE_KEY`, `SUPABASE_ACCESS_TOKEN`(사용자 JWT), `TEAM_TODO_ACTOR_ID`가 필요하다. 연결된 RLS 정책과 JWT의 사용자 식별이 일치해야만 작동한다. **서비스 역할/비밀 키를 CLI에 넣거나 공유하지 말 것.** 운영에서 X-Actor-ID 헤더 + 공유 API 키만 사용하는 방식은 강한 사용자 단위 인증이 아니므로, 외부 공개 전 사용자 JWT 검증과 권한 주체 매핑이 추가로 필요하다.

## 4. 테스트·한계

```bash
python -m pytest -q
python scripts/smoke_local.py  # 실제 127.0.0.1 서버/CLI/격리 SQLite 자동 검증
python -m app.kanban.inspect_database  # DATABASE_URL 필요
```

로컬 결과·라이브 DB 실패 사유: `docs/VALIDATION.md`. 로컬 실제 HTTP 전구간 시연 출력: `docs/SMOKE_RESULT.json`. 과제용 3분 발표 시나리오: `docs/DEMO_3_MIN.md`. **수업에서 시연 전 `python -m app.bootstrap`를 수행하고 서버/CLI를 켜 두면 된다.**

**실제로 확인하지 못한 사항**: 사용자 공유 Supabase 6개 테이블의 실제 제약/RLS, Postgres 트랜잭션 통합 테스트, 웹 프런트엔드 연결, Codex가 사용자의 실제 공유 보드에 카드를 저장하는 운영 시연. 원본 압축파일 밖의 코드는 제공되지 않았다. 과제 제출 마감과 발표 형식은 교수님의 최신 안내로 최종 확인한다. 이 문서에는 3분 발표 시연안을 준비했다.


## 5. 기존 과제 대비 추가한 검증 가능한 차별점

- 레퍼런스의 `projects`, `team_members`, `tasks` 모델을 **복제하지 않았다**. 우리 팀의 과제 #5 `users`, `boards`, `board_members`, `columns`, `cards`, `card_assignees` 6개 테이블을 그대로 사용한다.
- 상태는 새로운 `status` 값을 저장하지 않고 `column_id`로 표현한다. Todo/Doing/Done 컬럼 ID는 기존 보드의 값을 조회해서 사용한다.
- Codex가 남기는 계획·수행·테스트 결과·막힘 기록은 새 테이블을 가정하지 않는 활동 기록 API로 누적한다. 실제 기록 예시와 한계는 `docs/VALIDATION.md`를 참고한다.
- **로컬 API/CLI/DB 성공과 실제 공유 Supabase 통합 성공을 구분한다.** 공유 DB가 복구되지 않으면 발표에서 실 DB 연동이 완료됐다고 말하지 않는다.
- 원본 코드는 `kanban/`에 보존했고 제출 패키지에 원래 `kanban.zip`도 포함했다. 원본 10개 Python 파일의 SHA-256 비교 결과는 `docs/SOURCE_AUDIT.md`를 참고한다.

### Codex 작업 기록 시연 예시

```text
register(todo, same-key) -> 카드 ID 생성
log(plan) -> 실제 계획 기록
register(doing, same-key) -> 동일 카드 ID로 컬럼 이동
log(progress) -> 작업 파일/중간 결과 기록
실제 코드 수정 및 테스트
log(result) -> 근거 있는 테스트 결과 기록
register(done, same-key) -> 검증 성공한 경우에만 완료
get -> 최종 컬럼과 누적 기록 조회
```

**주의:** `register --description`은 기존 카드 설명을 대체할 수 있으므로, 기존 카드에는 `--description`을 반복해 사용하지 말고 `kanban log`로 활동 기록을 덧붙인다. 한도 5,000자를 넘어서는 장기 운영에서는 별도 댓글 테이블 + 감사 로그가 필요하다.

## 6. 과제 #7 최종 제출 추가 산출물

- 요구·기술·DB 명세: `docs/PRD.md`, `docs/TSD.md`, `docs/DATABASE.md`
- 테스트 시나리오: `docs/TEST_CASE.md`, `docs/TEST_CASE_CLI.md`
- CLI 명세: `docs/PRD_CLI.md`, `docs/TSD_CLI.md`
- 감사/한계: `docs/SECURITY_AUDIT.md`, `docs/PERFORMANCE_AUDIT.md`
- 발표용 슬라이드: `docs/ASSIGNMENT7_PRESENTATION.pptx` (슬라이드 5장, 3분 시연)
- Codex 규칙: `AGENTS.md`, `.agents/skills/kanban-task-tracker/SKILL.md`
- 자동검증: `.github/workflows/ci.yml` (GitHub 업로드 후에야 실제 CI 확인 가능)
- 현재 GitHub 업로드 상태: `docs/GITHUB_SUBMISSION.md`

### 실 DB 제약 최신 확인

Supabase의 `gcs-database-class` 복원 요청은 무료 프로젝트 활성화 한도(2개)에 의해 거절되었다. 기존 데이터는 삭제·변경하지 않았다. 따라서 본 제출 ZIP의 24개 테스트 PASS는 **SQLite 로컬 구현의 증거**이며, 실제 공유 DB 연동을 증명하지 않는다.
