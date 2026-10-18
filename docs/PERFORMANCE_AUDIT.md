# 성능 감사 — 범위와 제한

- 자동 테스트: 24개 API/CLI/SQLite 검사 통과. 별도 FastAPI 프로세스 + CLI 프로세스 로컬 E2E 통과.
- 라이브 PostgreSQL의 connection pool, 동시 사용자, 락 경합, 장기 부하 테스트 **미실시**. DB 프로젝트 비활성화 및 접근 제한으로 수행 불가.
- PostgreSQL row-level lock 및 카드 위치 유일성 제약은 실제 스키마/격리수준에 따라 추가 확인 필요.
- 실행 제안: 활성화된 테스트 DB와 분리된 테스트 보드를 확보한 뒤 10/50/100 동시 요청, p50/p95, 오류율, pool checkout wait, deadlock/timeout을 측정하여 결과를 여기에 첨부.
