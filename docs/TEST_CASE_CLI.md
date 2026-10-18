# TEST_CASE_CLI — CLI/E2E

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
