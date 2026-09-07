# NNS CTF — `triangle-platform`

**Category:** devsecoops (Kubernetes)

## Flag

```
NNS{M1Nn_bes7e_V3NN,_I_th1nK_7hat_I_MigHt_H4V3_a_kYv3RN0_4dDiCti0N_bUt_s0MeH0W_7her3_i5_No_W4y_7o_e5cap3_7he_yaM1_fUck3RY}
```

Run `./solve.sh https://triangle-platform-XXXX.chall.nnsc.tf`.

---

## 1. The target

A single `rancher/k3s` container (`supervisord` runs `k3s server`, `bootstrap`,
`registry`, `operator`, `frontend`). Only `127.0.0.1:7681` (the frontend) is
exposed.

```
frontend  :7681   /internal/*  ->  reverse-proxy to registry  (NO auth added)
                  /*           ->  static files, else reverse-proxy to kube-apiserver
                                   Authorization is injected ONLY if the client sent none:
                                       if r.Header.Get("Authorization") == "" { set console token }
```

`/out/token` is `kubectl -n tenant-a create token console` (24 h). So every
un‑authenticated `…/apis/…` request hits the apiserver as
**`system:serviceaccount:tenant-a:console`**, and any request that *does* carry an
`Authorization:` header is passed straight through with that bearer token.

### What `console` can do (`bootstrap/rbac.yaml`)

| resource | verbs | ns |
|---|---|---|
| `triangle.io/sites` | get list watch **create update patch delete** | `tenant-a` |
| `configmaps, pods, services` | get list watch | `tenant-a` |
| `services/proxy` | **get** | `tenant-a` |
| `pods/*` | get list watch create | `tenant-a` — *`pods/*` is not a valid RBAC string, grants nothing* |
| `apps/deployments` | get list watch | `tenant-a` |

No `domains`, no `secrets`, no `serviceaccounts/token`, no `pods/exec`, nothing
cross‑namespace. **The only real primitive is: create `Site` objects and read the
rendered `Deployment`/`Service` (incl. `services/proxy`).**

### The operator (`operator/*.go`)

A controller‑runtime operator watches `Site` (namespaced) and `Domain`
(cluster‑scoped).

* `decodeSite(spec.siteYAML)` — parses with **`gopkg.in/yaml.v3`**
  (`yaml.Unmarshal(data, &map[string]yaml.Node)` then per‑key `.Decode`).
* `claimZoneHost` — for `Site` *N* in namespace *ns* it server‑side‑applies a
  cluster `Domain` named `<ns>-<N>` with `spec.host = "<N>.sites.triangle.tld"`,
  `spec.siteRef = {ns, N}` — **unless** some *other* `Domain` already has that
  exact `spec.host` string (then it "bails" and creates nothing).
* `serving(all, site)` = claims whose `siteRef == site` and that are **not
  `contested`** (`contested` = another claim, **same raw `spec.host` string**,
  different `siteRef`).
* `syncOriginConfig(site, served)` — for every served claim it reads the Secret
  **`triangle-origins/origin-<canonicalHost(host)>`**, merges `.Data`, and writes
  it as `<site>-origin` in the site's namespace.
  ```go
  func canonicalHost(h string) string { return strings.ToLower(strings.TrimSuffix(h, ".")) }
  ```
  `canonicalHost` is applied **only here** (and in the registry). `claimZoneHost`
  and `contested` compare `spec.host` **raw**.
* `render` — an `nginxinc/nginx-unprivileged` pod that statically serves
  `cfg.Server.Root` / `cfg.Server.Index`. `AutomountServiceAccountToken:false`;
  the only token is a **projected** volume at `/var/run/triangle/token` with
  `Audience: cfg.audience()`. If `syncOriginConfig` produced a secret it is
  mounted at `/var/run/origin`. `ServiceAccountName: cfg.serviceAccountName()`.

```go
func platformDefaults() siteConfig { return siteConfig{ Target: Target{Plane: "control"}, ... } }
var planeAudiences = map[Plane]string{ "origin":"triangle.origin.v1", "edge":"triangle.edge.v1", "control":"" }
func (c siteConfig) audience() string { return planeAudiences[c.Target.Plane] }
func (c siteConfig) serviceAccountName() string {
    if len(c.Integrations) == 0 { return "tri-forms" }
    return integrationAccounts[c.Integrations[0]]   // forms→tri-forms analytics→… images→… edge→tri-edge
}
```

### Kyverno (`policies/*.yaml`)

Two `ValidatingPolicy` (`policies.kyverno.io/v1`, `failurePolicy: Fail`) on
`sites` CREATE/UPDATE. Both parse the YAML with the CEL function
`yaml.parse(object.spec.siteYAML)`, which in Kyverno is
**`sigs.k8s.io/yaml.Unmarshal`** → i.e. **`goyaml.v2` → JSON → `json.Unmarshal`**.

* `site-target-plane`: `!has(cfg.target.plane) || cfg.target.plane in ['origin','edge']`
* `site-integration-entitlement`: `!has(cfg.integrations) || cfg.integrations.all(i, i in ['forms','analytics'])`

### Where the flag is

`bootstrap.sh`:
```
kubectl -n triangle-origins create secret generic \
    origin-acme-invoices.sites.triangle.tld --from-literal="FLAG=${FLAG}"
```
`bootstrap/tenant-b.yaml` pre‑creates a cluster `Domain`
`tenant-b-acme-invoices` → `host: acme-invoices.sites.triangle.tld`,
`siteRef: {tenant-b, invoices}`. So `syncOriginConfig` mounts the flag into
`tenant-b/invoices` — a namespace `console` cannot touch.

To read the flag we must get `origin-acme-invoices.sites.triangle.tld` copied
into **`tenant-a`**, i.e. get a *served* `Domain` whose `siteRef` is a `tenant-a`
`Site` we own and whose `canonicalHost(spec.host) == "acme-invoices.sites.triangle.tld"`.

`claimZoneHost` can only ever emit `spec.host = "<sitename>.sites.triangle.tld"`,
and `<sitename>` is an RFC‑1123 name (lower‑case, no trailing dot) so
`canonicalHost` is the identity on it — the only match is `sitename == "acme-invoices"`,
which **bails** on tenant‑b's Domain. `console` cannot create `Domain`s. Dead end…
until we escalate.

---

## 2. Vuln A — `target: null` ⇒ token minted with the API‑server audience

`decodeSite` starts from `platformDefaults()` (`Plane: "control"`) and is supposed
to overwrite it:

```go
target, ok := nodes["target"]
if !ok { return site, errInvalidSite }
if err := target.Decode(&site.Target); err != nil { return site, errInvalidSite }
```

`Target` has a pointer‑receiver `UnmarshalYAML` that only ever accepts
`origin`/`edge`. **But `yaml.v3` never calls it for a null node.** In
`decode.go`:

```go
func (d *decoder) prepare(n *Node, out reflect.Value) (..., unmarshaled, good bool) {
    if n.ShortTag() == nullTag { return out, false, false }   // <-- returns BEFORE the Unmarshaler check
    ...
}
func (d *decoder) scalar(n *Node, out reflect.Value) bool {
    ...
    if resolved == nil { return d.null(out) }
}
func (d *decoder) null(out reflect.Value) bool {
    if out.CanAddr() { switch out.Kind() {
        case reflect.Interface, reflect.Ptr, reflect.Map, reflect.Slice:
            out.Set(reflect.Zero(out.Type())); return true } }
    return false          // <-- struct: NO-OP
}
```

So `target: null` (or `target:` / `target: ~`) makes `target.Decode(&site.Target)`
a **complete no‑op that returns `nil`**. `site.Target.Plane` stays `"control"`,
`planeAudiences["control"] == ""`, so the pod's projected token gets
`Audience: ""` → kubelet mints it with the **apiserver's own audiences**
(`https://kubernetes.default.svc.cluster.local`, `k3s`) → it authenticates
against the apiserver and passes the registry's `TokenReview` (which sends no
audiences).

Kyverno's `site-target-plane` **allows** it: `has(cfg.target.plane)` on a null
`cfg.target` evaluates to `false`, so `!has(...)` is `true`.

---

## 3. Vuln B — `<<` merge differential ⇒ `integrations: [edge]` past Kyverno

We want the pod's `ServiceAccountName` to be `tri-edge`, i.e. the operator must
see `integrations: [edge]` while Kyverno must not.

* **`yaml.v3` (operator):** in `mapping()`, `<<` is collected and applied **last**
  via `d.merge`, which builds `mergedFields` from *all* the parent's explicit
  keys — a merged key is **skipped if the parent set it explicitly**, regardless
  of order. Explicit always wins.
* **`goyaml.v2` (Kyverno / `sigs.k8s.io/yaml`):** `<<` is processed **at its
  position**; `d.merge` → `unmarshal(merge, out)` → `out.SetMapIndex(k, v)` which
  **overwrites**. An explicit key that appeared *before* the `<<` is clobbered by
  the merge.

```yaml
target: null
integrations:
  - edge            # operator keeps this  -> serviceAccountName = tri-edge
<<:
  integrations:
    - forms         # kyverno's goyaml.v2 overwrites -> sees ['forms'] -> ADMIT
server:
  root: /var/run/triangle
  index: token
```

(The operator's guard `integrations.Kind==SequenceNode && len(site.Integrations)!=len(integrations.Content)`
— which defeats the `[edge, null, null]` "padding" trick — is not tripped: the
explicit node is a 1‑element sequence and decodes to a 1‑element slice.)

Result: a `tenant-a/tri-edge` pod holding an **apiserver‑audience** token.
Exfiltrate it: the site's nginx `root` is `/var/run/triangle`, `index` is
`token`, so

```
GET /api/v1/namespaces/tenant-a/services/x1:80/proxy/token
```

returns the JWT (`sub: system:serviceaccount:tenant-a:tri-edge`,
`aud: [https://kubernetes.default.svc.cluster.local, k3s]`).

---

## 4. Escalation — `tri-edge` ➜ `tri-registry-sync`

`tri-edge` (`bootstrap/platform-rbac.yaml`):

* ClusterRole `triangle:edge`: `sites`, `domains` — get/list/watch (still **no**
  create).
* Role `triangle-edge` in `triangle-system`: **`secrets: [create, get]`**.

Classic move: create a **`kubernetes.io/service-account-token` Secret** for
another ServiceAccount and let the built‑in *TokenController* fill it in.

```jsonc
POST /api/v1/namespaces/triangle-system/secrets     // Authorization: Bearer <tri-edge>
{ "metadata": { "name": "rsync-tok",
                "annotations": { "kubernetes.io/service-account.name": "tri-registry-sync" } },
  "type": "kubernetes.io/service-account-token" }
```

A couple of seconds later `GET` the same Secret — `.data.token` is now a valid
legacy token for **`system:serviceaccount:triangle-system:tri-registry-sync`**,
which holds ClusterRole `triangle:registry-sync` → **`domains: [create, get, list, watch]`**.

---

## 5. Vuln C — `canonicalHost` is only applied on the read side

As `tri-registry-sync`, create a cluster `Domain` pointing at a `tenant-a` `Site`
we own, with a host that is **raw‑distinct** from tenant‑b's but **canonicalises
to the flag host**. The `Domain` CRD puts **no `pattern`** on `spec.host` (only
`maxLength: 253`), so a trailing dot is legal:

```jsonc
POST /apis/triangle.io/v1/domains                    // Authorization: Bearer <tri-registry-sync>
{ "metadata": { "name": "pwn-alias" },
  "spec": { "host": "acme-invoices.sites.triangle.tld.",      // <-- trailing dot
            "siteRef": { "namespace": "tenant-a", "name": "pwn" } } }
```

Now reconcile `Site tenant-a/pwn` (siteYAML `target: null` + `root: /var/run/origin`,
`index: FLAG`):

| check | value | result |
|---|---|---|
| `claimZoneHost` bail | `"pwn.sites.triangle.tld"` vs existing hosts | no match → **no bail**, `tenant-a-pwn` created |
| `contested(pwn-alias)` | needs another claim with raw host `"acme-invoices.sites.triangle.tld."` | none → **not contested** |
| `serving({tenant-a,pwn})` | `tenant-a-pwn` + `pwn-alias` | both served |
| `syncOriginConfig` | `origin-` + `canonicalHost("acme-invoices.sites.triangle.tld.")` = `origin-acme-invoices.sites.triangle.tld` | **flag Secret read**, merged into `tenant-a/pwn-origin`, mounted at `/var/run/origin` |

`bootstrap/tenant-b.yaml`'s Domain has raw host `acme-invoices.sites.triangle.tld`
(no dot), so it neither blocks `claimZoneHost` nor `contest`s our alias.

---

## 6. Read the flag

```
GET /api/v1/namespaces/tenant-a/services/pwn:80/proxy/FLAG
-> NNS{M1Nn_bes7e_V3NN,_I_th1nK_7hat_I_MigHt_H4V3_a_kYv3RN0_4dDiCti0N_bUt_s0MeH0W_7her3_i5_No_W4y_7o_e5cap3_7he_yaM1_fUck3RY}
```

---

## 7. Root causes / fixes

1. **`yaml.v3` skips a custom `UnmarshalYAML` on a null node.** `decodeSite`
   should reject a `target` that is not a mapping, or explicitly re‑validate
   `site.Target.Plane` against `{origin, edge}` (not against `planeAudiences`,
   which contains `control`). `platformDefaults().Plane` should not be a value
   with an empty audience.
2. **Two YAML parsers, one policy engine, one consumer.** `yaml.v3` vs
   `goyaml.v2` disagree on duplicate keys (error vs last‑wins) and on
   `<<`‑vs‑explicit precedence (explicit‑always‑wins vs positional‑overwrite).
   The admission policy must parse with the *same* library/semantics the
   consumer uses, or the consumer must feed the policy a normalised object.
3. **`canonicalHost` normalisation applied inconsistently.** The uniqueness /
   `contested` checks compare `spec.host` raw while the secret lookup canonicalises
   it. Normalise once, on write, and pattern‑constrain `Domain.spec.host`.
4. **`secrets: [create]` in a namespace that also hosts a privileged
   ServiceAccount** ⇒ trivial token minting via `kubernetes.io/service-account-token`
   Secrets. Scope the verb to `resourceNames`, disable legacy token secrets, or
   don't co‑locate.

## 8. Files

| file | purpose |
|---|---|
| `solve.sh` | full chain, `./solve.sh <instance-url>` → prints the flag |
| `src/operator/` | `types.go` (vuln A/B), `domain.go` (vuln C), `main.go`, `render.go` |
| `src/policies/` | the two Kyverno `ValidatingPolicy`s |
| `src/bootstrap/` | `rbac.yaml` (console), `platform-rbac.yaml` (tri-edge / tri-registry-sync), `tenant-b.yaml`, `serviceaccounts.yaml` |
| `src/frontend/main.go` | the Authorization pass‑through |
| `src/registry/main.go` | `allowedSubject`, audience‑less `TokenReview` |
| `src/crd/` | `domain.yaml` (no host `pattern`), `site.yaml` |
| `src/bootstrap.sh`, `src/supervisord.conf` | how the flag secret and processes are set up |
