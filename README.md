# Steel Browser for Hostinger

한국어 안내입니다. [English](README.en.md).

공식 Steel API/UI 이미지를 사용하며, 인증과 HTTPS 경로를 맞춘 별도 설치 패키지입니다.
기존 Buzz 프로젝트를 변경하지 않습니다. **로컬 Docker 검증을 완료했으며 Hostinger 실서버 검증은 남아 있습니다.**

## 선택 설치 및 지원 범위

**Steel Browser는 선택 사항입니다. buzz-agents의 필수 구성 요소가 아닙니다.**
기존 Buzz Relay와 buzz-agents만으로 AI 대화·협업·코드 실행을 사용할 수 있습니다.
VPS에서 웹사이트 화면을 조작하거나 브라우저 자동화가 필요한 경우에만 Steel 설치를 고려하세요.
Steel을 설치해도 Buzz 에이전트에 브라우저 도구가 자동 연결되지는 않으며, 별도 연결이 필요합니다.

Steel 자체는 Buzz나 buzz-agents 설치를 요구하지 않습니다.
이 패키지의 설치 전제는 **Hostinger Docker Manager와 실행 중인 Traefik**입니다.
Traefik이 없다면 먼저 준비해야 합니다.

## URL로 자동 설치

1. Hostinger Docker Manager에서 **Traefik이 실행 중인지** 확인합니다.
2. **컴포즈 → URL에서 Compose**에 다음 주소를 입력합니다.

   `https://raw.githubusercontent.com/volition79/steel-hostinger/main/compose.auto.yaml`

3. 프로젝트 이름은 `steel-browser`처럼 기존 프로젝트와 다른 이름을 사용합니다.
4. 지원되는 기본 Hostinger 구성에서는 **환경을 비워 둔 채 배포**합니다. 서버 주소와 최초 비밀번호를 자동 설정합니다.
5. 배포가 끝나면 프로젝트의 **열기**를 누릅니다. 표시되지 않으면 `bootstrap` 로그의 HTTPS 주소를 엽니다. 최초 인증서 발급에는 시간이 걸릴 수 있습니다.
6. 로그인 페이지에서 `auth-init` 로그에 표시된 최초 **비밀번호만** 입력합니다. 사용자 이름은 자동 처리됩니다. 브라우저 언어에 따라 한국어·영어 안내가 표시되며 직접 전환할 수도 있습니다.
7. Steel 화면에서 방문할 사이트를 열고 로그인합니다.

이 주소는 main 브랜치를 따릅니다. 특정 버전을 유지하려면 main 대신 안내받은 커밋 SHA를 사용하세요.
이미지는 공개된 digest로 고정되어 있으며 별도 빌드가 필요 없습니다.
로컬 Docker에서 Buzz 없이 자동 주소 설정·인증·Steel 접속을 검증했습니다. **실제 Hostinger의 URL 가져오기·열기·공인 인증서는 사용자 테스트가 남아 있습니다.**

## 자동 설치 동작과 조건

사용 흐름은 **URL로 배포 → 주소 자동 설정 → 열기 → 로그인**입니다.
`STEEL_HOST`와 비밀번호를 생략할 수 있도록 구현했습니다. 최초 비밀번호는 `auth-init` 로그에서 확인합니다.

- 실행 중인 Traefik 한 개, 활성화된 Docker provider, 식별 가능한 HTTPS 진입점·인증서 설정이 필요합니다.
- Docker 서버 이름 또는 Traefik의 `TRAEFIK_HOST`·기존 라우터에서 `srv번호.hstgr.cloud`를 찾습니다. Buzz는 필요하지 않습니다.
- 주소 후보가 없거나 여러 개이면 임의로 선택하지 않습니다. `bootstrap` 로그에 원인이 표시됩니다.
- VPS 기본 주소가 내부에서 `127.0.1.1` 같은 루프백으로 조회되면 [Google Public DNS의 HTTPS API](https://developers.google.com/speed/public-dns/docs/doh/json)로 두 주소의 공인 IP를 다시 비교합니다. 공인 조회에 실패하거나 IP가 다르면 통과시키지 않습니다. 로그에는 비교한 주소와 IP가 표시됩니다.
- DNS가 준비되지 않았거나 Traefik 설정을 확인할 수 없으면 설정을 보류합니다. 문제를 해결한 뒤 프로젝트를 다시 시작하세요.
- 첫 설정에서 확정한 주소와 네트워크는 재실행 시 유지합니다. 설정 변경이 감지되면 자동 덮어쓰기 대신 중단합니다.
- 자기 프로젝트의 gateway 라벨·네트워크만 변경합니다. 다른 프로젝트와 기존 데이터 볼륨은 변경하지 않습니다.
- 설치 도우미만 Docker 소켓과 자기 Compose 폴더에 접근합니다. **Docker 소켓 접근은 VPS의 컨테이너를 제어할 수 있는 관리자 수준 권한**입니다. 브라우저/API/UI에는 이 권한을 전달하지 않습니다.
- Traefik에 Docker provider를 파일로만 설정하여 활성화를 확인할 수 없는 구성, 다중 Traefik·다중 주소 후보는 현재 자동 지원 범위 밖입니다.

개발자 검증: `docker build -f Dockerfile.bootstrap -t steel-bootstrap:test .` 후 `python3 build_auto.py --image steel-bootstrap:test`로 개발용 파일을 생성합니다.
공개 파일은 `images.yaml`의 도우미 digest를 사용해 `python3 build_auto.py`로 생성합니다.

## 고급: 주소를 지정하는 수동 설치

1. Hostinger Docker Manager에서 Traefik이 실행 중인지 확인합니다.
2. 컴포즈 → URL에서 Compose에 아래 주소를 입력합니다.

   `https://raw.githubusercontent.com/volition79/steel-hostinger/main/compose.hostinger.yaml`

   이 주소는 main 브랜치의 파일입니다. 특정 버전을 유지하려면 `main`을 해당 커밋 SHA로 바꿉니다.
   파일 하나에 설정이 모두 들어 있어 별도의 파일 업로드나 이미지 빌드는 필요 없습니다.
3. 프로젝트 이름은 `steel-browser` 등 기존 프로젝트와 다른 이름을 사용합니다.
4. 환경 변수에 `STEEL_HOST`를 입력합니다. `STEEL_PASSWORD`는 선택 사항입니다. 환경이 비어 있으면 파일 가져오기는 가능하지만 초기화가 중단됩니다. `auth-init` 로그의 안내대로 환경을 입력하고 저장 및 배포하세요.

| 변수 | 입력 내용 |
|---|---|
| `STEEL_HOST` | 본인 VPS의 사용 가능한 호스트명. 예: `steel-browser.srv123456.hstgr.cloud`. `https://`, 포트, `/` 제외 |
| `STEEL_PASSWORD` | 선택: 16~72자의 한 줄 ASCII 비밀번호. 생략하면 최초 1회 무작위 생성하고 `auth-init` 로그에 표시. 기존 인증이 있으면 그대로 유지 |

5. 배포 후 `https://입력한-STEEL_HOST`를 엽니다. 관리자 화면의 **열기** 버튼 표시는 Hostinger 실서버에서 추가 확인해야 합니다.
6. 로그인 페이지에서 설정한 비밀번호 또는 `auth-init` 로그의 최초 비밀번호만 입력합니다. 로그를 타인에게 공유하지 마세요.
7. Steel의 기본 브라우저 화면이 표시되면 화면 안쪽 주소창에 방문할 주소를 입력합니다.

호스트명은 본인의 VPS를 가리켜야 하며 Traefik의 `websecure` 및 `letsencrypt` 설정이 필요합니다.
Hostinger가 별도 Docker 네트워크에 연결된 Traefik을 사용하는 환경이라면 공유 네트워크 연결을 추가해야 합니다.
현재 패키지는 확인된 Hostinger의 host-network Traefik 구성을 대상으로 합니다.

## 사용·업데이트

- Steel이 실행하는 브라우저는 VPS에 있습니다. 그 화면에서 사이트에 직접 로그인합니다.
- 이 패키지 설치만으로 Buzz 에이전트에 브라우저 도구가 자동 연결되지는 않습니다. 도구 연결은 별도 단계입니다.
- API·UI·WebSocket 모두 같은 인증을 거칩니다. API를 호출하는 자동화 도구도 인증 정보를 전달해야 합니다.
- 로그·다운로드·캐시 볼륨은 유지됩니다. 기본 브라우저 프로필은 별도 `browser` 볼륨에 저장합니다. 사이트의 자체 만료·로그아웃 및 별도 생성 세션까지 유지된다고 보장하지는 않습니다. 기존 버전의 임시 프로필은 자동 이전하지 않으므로 업그레이드 후 사이트 재로그인이 필요할 수 있습니다.
- 업데이트 전 작업을 끝내고 볼륨을 백업합니다. 같은 프로젝트에서 새 패키지로 편집·배포하고 볼륨은 삭제하지 않습니다.
- 이미지를 digest로 고정했으므로 Docker Manager의 업데이트 버튼만으로 새 버전으로 바뀌지 않습니다.
- 비밀번호 변경은 환경 변수 수정 후 재배포합니다. `auth-init`이 성공해야 새 게이트웨이가 시작됩니다.
  그다음 게이트웨이를 다시 시작하여 이미 열린 WebSocket 연결도 끊습니다. 새 비밀번호는 재시작만으로 적용되지 않습니다. 브라우저가 이전 인증을 기억하면 새 시크릿 창에서 접속합니다.

## 문제 해결

- 배포 실패: `auth-init` 로그에서 비밀번호 길이 확인. 환경 변수 누락도 확인합니다.
- 502: API/UI가 기동하는 동안 잠시 기다린 뒤 새로고침합니다. 계속되면 해당 컨테이너 로그를 확인합니다.
- 빈 브라우저 화면: 개발자 도구에서 WebSocket이 `wss://본인호스트/…`인지 확인합니다. HTTP 주소로 접속하지 않습니다.
- 인증 실패: 설치 비밀번호를 확인하세요. Hostinger 계정 비밀번호가 아닙니다. API 도구에서 Basic 인증을 사용할 때 사용자 이름은 `steel`입니다.
- 이미지 다운로드/브라우저 실행에는 RAM과 디스크 여유가 필요합니다. 기존 AI 봇과 자원을 함께 사용하므로 먼저 여유 용량을 확인합니다.

## 개발 및 검증

Python 3 + PyYAML: `python3 build_compose.py`로 배포 파일을 생성합니다.
`python3 -m unittest discover -s tests -v`로 패키지 계약을 검사합니다.
실행 검증 범위와 남은 항목은 `VERIFICATION.md`에 기록합니다.

참조: [Steel 공식 소스](https://github.com/steel-dev/steel-browser),
[공식 Docker 안내](https://docs.steel.dev/overview/self-hosting/docker).

## 운영 한도와 복구

- 프로젝트 이름은 설치 후 유지하세요. 이름을 바꾸면 별도의 볼륨이 만들어져 새 설치처럼 보일 수 있습니다.
- 비밀번호 분실: 환경에 새 `STEEL_PASSWORD`를 넣고 저장 및 배포한 뒤 gateway를 다시 시작하세요. 인증 볼륨을 삭제하지 마세요.
- 브라우저 API 메모리 상한은 기본 2GiB입니다. 필요하면 환경에 `STEEL_MEMORY_LIMIT=3g`처럼 설정 후 재배포합니다. VPS 여유 메모리를 확인하세요. 상한은 다른 작업 보호용이며, 브라우저 메모리 부족을 없애지는 않습니다.
- 게이트웨이 요청 제한은 전체 합계 초당 20회, 일시 초과 60회입니다. 429이면 잠시 기다린 뒤 재시도하세요. 사용자별 제한은 아닙니다.
- 게이트웨이로 전송하는 HTTP 요청 본문은 최대 128MiB입니다. 원격 브라우저가 외부 사이트에 직접 보내는 업로드의 한도는 해당 사이트가 정합니다.
- 데이터 수신이 없는 연결은 1시간 후 끊길 수 있습니다. 화면을 새로고침하고 재연결하세요. 작업 총시간 제한은 아닙니다.
- 프로필은 이 패키지의 API 하나만 사용해야 합니다. 시작 시 독점 잠금을 확보한 뒤 이전 실행의 Chromium 잠금을 정리합니다. 다른 서비스·구버전과 프로필 볼륨을 동시에 공유하지 마세요. 업데이트는 기존 API를 종료한 후 교체합니다. 잠금 충돌 종료 코드 73이면 기존 실행을 확인하세요.
- 상태 검사는 API뿐 아니라 실제 Chromium 준비 여부도 확인합니다. `unhealthy` 표시만으로 Docker가 자동 재시작하지는 않습니다.
- 갑작스러운 종료 직전의 쿠키·입력 내용은 디스크에 저장되지 않았을 수 있습니다. 사이트 로그인 유지를 보장하는 백업 기능은 아닙니다.

## 초기 버전의 dns_mismatch 복구

기본 VPS 주소가 127.0.1.1로 조회되어 배포가 실패했다면, 기존 프로젝트의 **관리 → YAML 편집기**에서 `bootstrap`의 `image`만 수정판의 이미지 참조로 교체하고 배포하세요. 프로젝트 이름·볼륨·다른 서비스를 삭제하거나 변경하지 않습니다. 재시작만으로는 digest가 고정된 구버전이 업데이트되지 않습니다.

```text
ghcr.io/volition79/steel-hostinger-bootstrap@sha256:3476916882e6b0b1144c42e6bbba91b164ab5e214a8e04b97be9bc06906246bc
```

## 비밀번호 전용 로그인 화면으로 업데이트

기존 프로젝트의 YAML을 새 `compose.auto.yaml` 내용으로 교체하고 **같은 프로젝트 이름과 환경 변수·볼륨을 유지한 채 배포**하세요. 이 변경에는 `login` 서비스와 gateway 설정이 포함되므로 bootstrap 이미지 한 줄만 교체해서는 적용되지 않습니다. 사용자 지정 설정이 있으면 해당 변경점을 보존하세요. 기존 설치 비밀번호를 그대로 사용합니다.

브라우저 로그인은 최대 12시간 유지됩니다. login 서비스 재시작 후에는 다시 로그인합니다. 비밀번호 변경 시 이전 로그인 세션은 다음 요청부터 무효가 됩니다. 이미 열린 연결을 종료하려면 gateway를 다시 시작하세요. 자동화 도구는 기존 `steel` 사용자와 비밀번호를 이용한 명시적인 Basic 인증을 계속 사용할 수 있습니다.
