RAPPER JUNG DESIGN RADAR v0.5 - 배포용 파일

기존 저장소의 index.html 파일을 이 패키지의 index.html로 교체하고,
data/entries.json, scripts/prune.py, .github/workflows/prune.yml을 경로 그대로 추가하세요.

주의:
- 자동으로 오래된 데이터 레코드를 삭제하지만 Git 커밋 기록에는 이전 데이터가 남습니다.
  따라서 GitHub 저장소에서의 '완전 삭제'는 아닙니다.
- 30일 경과 자료를 Git 기록에서도 삭제하려면 별도 저장 구조가 필요합니다.
- 외부 이미지 파일은 저장하지 않고 링크만 표시합니다.
- 실제 레퍼런스 수집, 이미지 확인, 알림 기능은 미구현입니다.
- GitHub Actions의 쓰기 권한은 저장소 Settings > Actions > General > Workflow permissions에서
  Read and write permissions로 설정해야 자동 커밋이 가능합니다.
- 일정 실행은 GitHub의 사정에 따라 지연되거나 누락될 수 있습니다.
