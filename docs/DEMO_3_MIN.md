# 과제 #7 | 3분 발표·라이브 시연 대본

> **사전 준비**: 데모는 격리된 SQLite DB로 진행하며, 실제 Supabase 연동 성공으로 설명하지 않는다. `python -m app.bootstrap`에서 UUID 값을 기록하고, 다른 터미널에서 `TEAM_TODO_API_KEY=demo-key`를 설정한 뒤 `python -m uvicorn app.main:app --host 127.0.0.1 --port 8000` 실행. 시연 터미널도 동일 키를 환경변수로 설정한다. 아래 `<...>`를 자신의 부트스트랩 출력값으로 치환.

| 시간 | 화면·조작 | 발표 멘트 |
|---|---|---|
| 0:00–0:30 | `README.md` → 폴더 구조 | "과제 #5의 간반보드 DB 모델을 기반으로, 제공된 기존 소스는 보존하고 실행용 FastAPI 서버와 Typer CLI를 추가했습니다. 사용자, 보드, 컬럼, 카드를 관계형으로 연결했습니다." |
| 0:30–1:05 | `http://127.0.0.1:8000/docs`에서 GET `/api/v1/boards` 엔드포인트, GET `/api/v1/cards/{card_id}` 탐색 | "FastAPI에서 기존 6개 테이블을 다루며, 보드 멤버만 조회하고 편집 권한이 있는 멤버만 카드를 변경할 수 있습니다. 모든 API가 OpenAPI 문서로 제공됩니다." |
| 1:05–1:50 | 터미널: 아래 생성·목록 명령 실행 | "같은 API를 CLI에서도 실행합니다. 텍스트와 JSON 모드를 모두 지원하고 카드가 실제 로컬 DB에 저장됩니다." |
| 1:50–2:25 | `register` 동일 작업 키로 2회 호출해 카드 ID 일치 확인 후 `log --kind plan/progress/result` 기록을 `get`으로 확인 | "Codex Skill을 이용하면 작업을 시작/진행/완료에 맞춰 등록합니다. 같은 작업 키를 재사용하면 카드가 중복되지 않습니다. 계획·작업·결과도 기존 카드 설명에 누적하고 재조회합니다." |
| 2:25–2:45 | `pytest -q` 결과(24 tests) / `docs/VALIDATION.md` | "API·CLI·DB 접근 통합 테스트가 통과했고, 조회 권한과 외래키도 검증했습니다." |
| 2:45–3:00 | VALIDATION의 '미완료' | "다만 실제 Supabase는 접근 오류로 스키마 검증 및 쓰기 테스트를 완료하지 못해, 이번 결과를 로컬 검증과 공유 DB 미검증으로 구분했습니다." |

## 시연용 CLI 명령

CLI 터미널에 `TEAM_TODO_ACTOR_ID`, `TEAM_TODO_API_KEY`를 환경변수로 먼저 설정하면 아래처럼 입력한다.

```bash
python -m app.cli --text kanban columns <BOARD_UUID>
python -m app.cli --json kanban create <BOARD_UUID> --column-id <TODO_UUID> --title "과제7 API 구현"
python -m app.cli --json kanban list <BOARD_UUID>
python -m app.cli --json kanban register <BOARD_UUID> --column-id <TODO_UUID> --work-key assignment7-demo --title "Codex 간반 기록"
# 위 JSON의 id를 CARD_UUID로 복사
python -m app.cli --json kanban log <CARD_UUID> --kind plan --message "API/CLI/DB 검증 계획"
python -m app.cli --json kanban register <BOARD_UUID> --column-id <DOING_UUID> --work-key assignment7-demo --title "Codex 간반 기록"
python -m app.cli --json kanban log <CARD_UUID> --kind progress --message "CLI HTTP 호출 및 테스트 실행"
python -m pytest -q
# 결과가 실제 통과했을 때만:
python -m app.cli --json kanban log <CARD_UUID> --kind result --message "pytest 24 passed"
python -m app.cli --json kanban register <BOARD_UUID> --column-id <DONE_UUID> --work-key assignment7-demo --title "Codex 간반 기록"
python -m app.cli --json kanban get <CARD_UUID>
```

**예상 질문 대응**: (1) "CLI와 API 차이는?" → CLI가 HTTP 클라이언트이고 실제 저장은 FastAPI→SQLAlchemy→DB가 담당. (2) "기존 코드 지웠나?" → 원본 `kanban/` 보관, `app/kanban/` 사본에 보안·JSON 변경만 적용. (3) "Supabase 진짜 공유되나?" → 이번 세션에서 원격 SQL 연결에 실패해 확인하지 못함. SQLite 테스트는 Supabase 성공의 증거가 아님.


### 발표 정확성 메모

이 시나리오를 **사람이 수동으로 CLI 시연**하는 것과 **Codex 에이전트가 실제 Skill을 사용해 기록한 것**은 구별해야 한다. 현재 패키지에는 Skill 파일과 동작 가능한 CLI가 있지만, 사용자 실제 Codex 세션에서 원격 공유 보드 기록에 성공했다는 증거는 없다. 데모 DB는 SQLite이므로 레퍼런스 팀의 Supabase 성공 사례를 우리 팀 실적으로 발표하지 않는다.
