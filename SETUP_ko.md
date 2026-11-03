# 저장소 올리기 — 한 번만, 15분

1. GitHub에서 새 저장소 `dados-beneficios-br`를 **Public**으로 만든다. 가능하면 개인 계정 대신 무료 조직 `Ditail Labs` 아래에 둔다(개발자 실명 노출 방지).
2. 이 폴더 안의 파일을 전부 올린다: 저장소 화면 → Add file → Upload files → 폴더 안 내용을 통째로 끌어다 놓기 → Commit.
   - `.github` 폴더가 안 올라가면: Add file → Create new file → 이름 칸에 `.github/workflows/atualizar-dados.yml` 입력 → 이 폴더의 같은 파일 내용을 붙여넣기 → Commit.
3. Settings → Pages → Source = Deploy from a branch, Branch = `main`, 폴더 = `/docs` → Save.
4. Settings → Actions → General → Workflow permissions = **Read and write permissions** → Save.
5. Actions 탭 → `atualizar-dados` → Run workflow를 한 번 누른다. 초록 체크면 끝.
6. 공개 주소 = `https://<계정 또는 조직>.github.io/dados-beneficios-br/` · 앱이 읽는 파일 = 그 주소 뒤 `v1/all.json`. 이 주소를 Claude에게 알려주면 앱 코드에 넣는다.

이후엔 손댈 것 없다. 매일 아침 공식 발표를 읽고, 규칙과 맞으면 데이터만 갱신한다.
다르거나 못 읽으면 저장소에 이슈가 생기고 메일이 온다 → 그 메일을 Claude 세션에 붙여넣으면 확인해서 `data/overrides.json` 수정본을 준다.
