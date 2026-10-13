# Shared by initialization and gateway startup. Never echo untrusted input.
if ! printf '%s\n' "$STEEL_HOST" | awk '
  length($0)>253 || length($0)<4 { exit 1 }
  /[^a-zA-Z0-9.-]/ { exit 1 }
  { n=split($0,a,"."); if(n<2) exit 1;
    for(i=1;i<=n;i++) if(length(a[i])<1 || length(a[i])>63 || a[i] ~ /^-/ || a[i] ~ /-$/) exit 1;
    if(tolower(a[n])=="invalid") exit 1;
    count++ }
  END { if(count!=1) exit 1 }'; then
  echo 'SETUP REQUIRED: Docker Manager > this project > Manage > Environment' >&2
  echo 'Set STEEL_HOST to your VPS hostname (no https://, port or path), then Save and deploy.' >&2
  echo '설정 필요: 관리 > 환경에 STEEL_HOST=본인서버주소 입력 후 저장 및 배포하세요.' >&2
  exit 1
fi
