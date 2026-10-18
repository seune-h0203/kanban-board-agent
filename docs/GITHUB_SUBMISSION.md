# GitHub 제출 상태

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
