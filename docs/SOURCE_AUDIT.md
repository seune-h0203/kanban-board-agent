# 원본 대비 소스 보존 기록

- 입력: 사용자 이전 대화 파일 `kanban.zip` (17개 ZIP 엔트리, 그중 Python 소스 10개).
- `kanban/`: 원본 `.py` 10개 파일의 바이트 그대로 유지.
- `app/kanban/`: 사본 10개(6개 무수정, 4개 최소 보완): `api.py`, `cli.py`, `shared_cli.py`, `tracking.py`.
- 원본에는 `app/db/base.py`, `app/db/session.py`, `app/cli.py`, `app/main.py`가 없어 새로 구현했다.
- 원격 기존 DB는 변경·삭제하지 않았다.

이 패키지는 **`kanban.zip`을 기반으로 실행용 통합 구조를 보완한 것**이다. 미제공된 사용자 저장소의 전체 변경 집합을 자동 병합한 것은 아니다.

## 원본 Python 소스 SHA-256 확인 (최종본)

- `kanban/api.py` — 동일: **True**, SHA-256 `a1993280d0a80d47368863f98aff9fac376a0e68e5b251f391b39072df28cd15`
- `kanban/cli.py` — 동일: **True**, SHA-256 `7a5a5c240ee756d2f76810717b9abf76dcbc08ec6bf8f83b9be507b8514e5351`
- `kanban/inspect_database.py` — 동일: **True**, SHA-256 `310da9e8c68af5afe434b58dfcb90c41b30da996a57dd5a779b79b07028efd06`
- `kanban/models.py` — 동일: **True**, SHA-256 `0b223a92646b0d6b87f82fb44a3966f211b943763f9c87dd248f3e1cb19624cb`
- `kanban/schemas.py` — 동일: **True**, SHA-256 `49db04fdd2b8bf026c0c0cadc203f42a97302a5c03809c3044a70bd98f52c2e1`
- `kanban/seed.py` — 동일: **True**, SHA-256 `9637baaf277c3fe0c93f0b24f52f8b12a95d74ff31b260ff4544fc57cdb384dd`
- `kanban/shared.py` — 동일: **True**, SHA-256 `43ec7d4ff18563d0685c0ba763d6a16a677ec727060ab87ccc54c594187a4e0c`
- `kanban/shared_cli.py` — 동일: **True**, SHA-256 `7255b78f61a254c38b1ad2f767e2d4e06c115195324dca3f8885d91d9c2a92e9`
- `kanban/tracking.py` — 동일: **True**, SHA-256 `b0cab65299087e596de243a68d1b0c3b4a1956c7227141b9c48cfdb209d4e9e5`
- `kanban/__init__.py` — 동일: **True**, SHA-256 `96cf9128888e9c5daca8197e9fd149774247e7c5879210cbfa6cc987871252fa`

독립 검증: `source-original-kanban.zip` 각 `.py`를 압축 해제된 `kanban/`와 바이트 단위 비교. 10/10 동일, 원본 삭제 없음.
