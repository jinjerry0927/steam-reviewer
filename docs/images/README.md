# 이미지 자산

로고·스크린샷 등 README에서 참조하는 이미지를 여기에 둡니다.

## 로고

- 파일명: `logo.png` (권장 1024×1024, 투명 배경 PNG)
- 이 폴더에 넣고 커밋하면 됩니다. (`.gitignore`가 `docs/images/*.png`는 추적하도록 예외 처리돼 있음)

## README에서 참조하는 법

GitHub와 PyPI **둘 다**에서 보이게 하려면 상대경로가 아니라 **절대 raw URL**을 써야 합니다
(PyPI는 상대경로 이미지를 렌더링하지 않음):

```markdown
<p align="center">
  <img src="https://raw.githubusercontent.com/jinjerry0927/steam-reviewer/main/docs/images/logo.png" width="180" alt="steam-reviewer logo">
</p>
```

로고를 추가하면 위 스니펫을 README 최상단(제목 위)에 넣어드리겠습니다.
