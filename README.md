# Steel Browser for Hostinger

한국어 안내입니다. [English](README.en.md).

공식 Steel API/UI 이미지를 사용하며, 인증과 HTTPS 경로를 맞춘 별도 설치 패키지입니다.
기존 Buzz 프로젝트를 변경하지 않습니다. **로컬 Docker 검증을 완료했으며 Hostinger 실서버 검증은 남아 있습니다.**

## 설치

1. Hostinger Docker Manager에서 Traefik이 실행 중인지 확인합니다.
2. 컴포즈 → URL에서 Compose에 아래 주소를 입력합니다.

   `https://raw.githubusercontent.com/volition79/steel-hostinger/main/compose.hostinger.yaml`

   이 주소는 main 브랜치의 파일입니다. 특정 버전을 유지하려면 `main`을 해당 커밋 SHA로 바꿉니다.
   파일 하나에 설정이 모두 들어 있어 별도의 파일 업로드나 이미지 빌드는 필요 없습니다.
3. 프로젝트 이름은 `steel-browser` 등 기존 프로젝트와 다른 이름을 사용합니다.
4. 환경 변수에 아래 두 값을 입력합니다.

| 변수 | 입력 내용 |
|---|---|
| `STEEL_HOST` | 본인 VPS의 사용 가능한 호스트명. 예: `steel-browser.srv123456.hstgr.cloud`. `https://`, 포트, `/` 제외 |
| `STEEL_PASSWORD` | 이 브라우저 전용 비밀번호. 16자 이상. 영문·숫자로 만든 긴 무작위 값 권장 |

5. 배포 후 `https://입력한-STEEL_HOST`를 엽니다. 관리자 화면의 **열기** 버튼 표시는 Hostinger 실서버에서 추가 확인해야 합니다.
6. 브라우저의 인증 창에 사용자 이름 **steel**, 위 비밀번호를 입력합니다.
7. Steel의 기본 브라우저 화면이 표시되면 화면 안쪽 주소창에 방문할 주소를 입력합니다.

호스트명은 본인의 VPS를 가리켜야 하며 Traefik의 `websecure` 및 `letsencrypt` 설정이 필요합니다.
Hostinger가 별도 Docker 네트워크에 연결된 Traefik을 사용하는 환경이라면 공유 네트워크 연결을 추가해야 합니다.
현재 패키지는 확인된 Hostinger의 host-network Traefik 구성을 대상으로 합니다.

## 사용·업데이트

- Steel이 실행하는 브라우저는 VPS에 있습니다. 그 화면에서 사이트에 직접 로그인합니다.
- 이 패키지 설치만으로 Buzz 에이전트에 브라우저 도구가 자동 연결되지는 않습니다. 도구 연결은 별도 단계입니다.
- API·UI·WebSocket 모두 같은 인증을 거칩니다. API를 호출하는 자동화 도구도 인증 정보를 전달해야 합니다.
- 로그·다운로드·캐시 볼륨은 유지됩니다. **세션 재생성/컨테이너 재시작 후 사이트 로그인이 유지된다고 보장하지 않습니다.**
- 업데이트 전 작업을 끝내고 볼륨을 백업합니다. 같은 프로젝트에서 새 패키지로 편집·배포하고 볼륨은 삭제하지 않습니다.
- 이미지를 digest로 고정했으므로 Docker Manager의 업데이트 버튼만으로 새 버전으로 바뀌지 않습니다.
- 비밀번호 변경은 환경 변수 수정 후 재배포합니다. `auth-init`이 성공해야 새 게이트웨이가 시작됩니다.
  브라우저가 이전 인증을 기억하면 새 시크릿 창에서 접속합니다.

## 문제 해결

- 배포 실패: `auth-init` 로그에서 비밀번호 길이 확인. 환경 변수 누락도 확인합니다.
- 502: API/UI가 기동하는 동안 잠시 기다린 뒤 새로고침합니다. 계속되면 해당 컨테이너 로그를 확인합니다.
- 빈 브라우저 화면: 개발자 도구에서 WebSocket이 `wss://본인호스트/…`인지 확인합니다. HTTP 주소로 접속하지 않습니다.
- 인증 실패: 사용자 이름은 `steel`입니다. Hostinger 계정 비밀번호가 아닙니다.
- 이미지 다운로드/브라우저 실행에는 RAM과 디스크 여유가 필요합니다. 기존 AI 봇과 자원을 함께 사용하므로 먼저 여유 용량을 확인합니다.

## 개발 및 검증

Python 3 + PyYAML: `python3 build_compose.py`로 배포 파일을 생성합니다.
`python3 -m unittest discover -s tests -v`로 패키지 계약을 검사합니다.
실행 검증 범위와 남은 항목은 `VERIFICATION.md`에 기록합니다.

참조: [Steel 공식 소스](https://github.com/steel-dev/steel-browser),
[공식 Docker 안내](https://docs.steel.dev/overview/self-hosting/docker).
