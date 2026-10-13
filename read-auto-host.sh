# No shell evaluation of discovered content. The helper atomically publishes one hostname.
for attempt in $(seq 1 120); do
  if [ -s /setup/host ]; then break; fi
  sleep 5
done
test -s /setup/host || { echo 'Steel address setup pending. Check bootstrap logs / bootstrap 로그를 확인하세요.' >&2; exit 1; }
STEEL_HOST=$(cat /setup/host)
export STEEL_HOST
