# TEST_CASE — API 및 DB 수용 기준

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
