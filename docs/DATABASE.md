# DATABASE — 기존 과제 #5 구조 유지

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
