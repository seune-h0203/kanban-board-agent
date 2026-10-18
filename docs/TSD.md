# TSD — 구조와 구현 판단

## 아키텍처
사용자/Codex → Typer CLI (HTTP) → FastAPI (SQLAlchemy) → 기존 PostgreSQL(Supabase) 또는 개발용 SQLite. Swagger: `/docs`, OpenAPI: `/openapi.json`.

## 데이터 일관성
board_members의 owner/editor는 쓰기 가능, viewer는 조회만 가능. 카드의 `column_id`가 상태를 나타낸다. 카드 할당자는 같은 보드의 구성원만 가능하며 잘못된 cross-board 업데이트를 차단한다. `register`는 보드+작성자+work-key 조합을 이용해 중복 생성을 줄인다. 기존 카드 설명에 로그를 누적하므로 길이 제한과 수정 가능성이 있다.

## 환경
Python 3.11–3.13, FastAPI, SQLAlchemy, Typer, httpx, pytest. 크로스플랫폼 실행: `python -m app.cli`. `TEAM_TODO_API_KEY`는 서버에서 필수(격리 로컬 시연 예외). PostgreSQL은 실제 스키마 검증 전 DDL 금지. 인터넷 공개 전에 JWT 기반 신원 확인 필요.

## 로컬 실행
`python -m pip install -e '.[dev]'`; `python -m app.bootstrap`; `python -m uvicorn app.main:app --host 127.0.0.1 --port 8000`; `python -m pytest -q`; `python scripts/smoke_local.py`.
