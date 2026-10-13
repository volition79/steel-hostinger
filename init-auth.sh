umask 077
# VALIDATE_HOST
if [ -n "$STEEL_PASSWORD" ]; then
  # htpasswd -i is line-oriented; only printable ASCII, 16..72 bytes.
  if ! printf '%s\n' "$STEEL_PASSWORD" | LC_ALL=C awk '
    length($0)<16 || length($0)>72 || /[^ -~]/ { exit 1 }
    { count++ } END { if(count!=1) exit 1 }'; then
    echo 'STEEL_PASSWORD must contain 16..72 printable ASCII characters on one line.' >&2
    exit 1
  fi
elif [ -s /auth/users ]; then
  echo 'Existing Steel password preserved. 기존 비밀번호를 유지합니다.'
  exit 0
else
  RANDOM_HEX=$(od -An -N24 -tx1 /dev/urandom)
  STEEL_PASSWORD=$(printf '%s' "$RANDOM_HEX" | tr -d ' \n')
  test "${#STEEL_PASSWORD}" -eq 48 || { echo 'Password generation failed' >&2; exit 1; }
  case "$STEEL_PASSWORD" in *[!0-9a-f]*) echo 'Invalid entropy output' >&2; exit 1;; esac
  GENERATED=1
fi
trap 'rm -f /auth/users.new' EXIT
printf '%s\n' "$STEEL_PASSWORD" | htpasswd -i -B -C 10 -c /auth/users.new steel
chmod 644 /auth/users.new
mv /auth/users.new /auth/users
if [ "${GENERATED:-0}" = 1 ]; then
  echo 'Steel first login / 최초 로그인 (store privately / 안전하게 보관):'
  echo 'Username: steel'
  printf 'Password: %s\n' "$STEEL_PASSWORD"
  echo 'If lost: set STEEL_PASSWORD in Environment and Save and deploy. Do not delete volumes.'
else
  echo 'Steel password configured. 비밀번호 설정 완료.'
fi
