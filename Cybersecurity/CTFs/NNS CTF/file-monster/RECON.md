# file-monster — recon notes (WIP, not solved)

## Mechanic
- `POST /upload` (multipart `file`): filename must match `^[a-zA-Z][a-zA-Z0-9.]*$`
  (letters, digits, dots; leading letter). Writes `/tmp/<name>` with content =
  `uploadText.replaceAll('"','').replaceAll("'",'').replaceAll('`','').replace('FLAG', process.env.FLAG)`.
  Refuses if `/tmp/<name>` already exists ("Filename is already in use" = **existence oracle**).
  Then `new FileModel({name}).save()` (mongoose -> `file-monster.files`, doc = `{_id,name,__v}`).
- `GET /files`: dumps all `{_id,name,__v}`.
- `GET /` HTMLBundle, `GET /robots.txt` static Response. That's every route.
- App connects to mongod as **admin** over unix socket `/tmp/mongodb-27017.sock`.
- MongoDB also exposed externally (TLS proxy -> 27017) as read-only `viewer:viewer` on `file-monster`.
- Runtime: Bun 1.3.14 `--compile --minify --bytecode` binary, running as **root**,
  inside the `mongo:8.2.10` image. mongod runs as `mongodb`. CWD almost certainly `/`.
- `robots.txt` contains: "does not require brute force ... solution should not rely on guesswork."

## The blocker
`process.env.FLAG` only ever lands in `/tmp/<name>` file content. Need a read of that
file (or of `/proc/<pid>/environ`). Found no such primitive.

## Ruled out (tested against live instance)
- **Path traversal in filename**: bulletproof. Tried `../`, `..\`, `%2e%2e%2f`,
  `filename*` (RFC5987 — Bun ignores it), quoted-pairs `\/`, CR/LF/NUL/tab/ctrl bytes,
  obs-fold headers, dup `Content-Disposition`, dup `filename`, unquoted values,
  trailing `\n` (JS `$` is absolute, rejects it), overlong UTF-8. Regex + Bun parser
  never let `/`, `\`, `-`, `_`, `%` or a leading `.` through. `filename=""` -> `file.name`
  becomes the literal string `"undefined"`.
- **Web read-back of `/tmp`**: no route. `/tmp/x`, `/x`, `/files/x`, `/download/x`,
  `/read`, `/cat`, `/f/x`, param routes, `/_bun/*`, `/health`, `/debug`, etc. all 404.
  Static traversal on `/chunk-*.css` / `/robots.txt` (`..%2f`, `/../`, `....//`) all 404.
- **Shadowing static routes**: uploading `/tmp/robots.txt`, `/tmp/index.html`,
  `/tmp/favicon.ico` does NOT change `/robots.txt`, `/`, `/favicon.ico` (Response/HTMLBundle
  are built once at startup from the embedded VFS).
- **`/tmp` is a plain empty dir** (not symlinked to `/`; `etc`,`bin`,`usr`,`data` all "new").
  Only real occupant is the mongo socket (hyphenated -> unnameable).
- **mongod dbPath is NOT `/tmp`** (`WiredTiger*`, `mongod.lock`, `storage.bson` all "new").
- **MongoDB `viewer`**: pure `read` on `file-monster` only. Privileges =
  `changeStream,collStats,dbHash,dbStats,find,killCursors,listCollections,listIndexes,
  listSearchIndexes,planCacheRead,performRawDataOperations`. Denied: everything on
  `admin`/`local`/`config`, `serverStatus`, `hostInfo`, `getCmdLineOpts`, `getLog`,
  `getParameter` (any), `validate`, `usersInfo`, `$currentOp{allUsers}`, `$listCatalog`,
  `$unionWith`/`$lookup` cross-db, all writes (`insert`/`$out`/`createCollection`/`dropDatabase`).
  No replica set -> no change streams. No weak admin creds; no-auth conn gets nothing.
- **mongod server-side JS** (`$where` / `$function` / `mapReduce` / `$accumulator`): fully
  sandboxed mozjs. `globalThis` = `Function,Object,eval,sleep,gc,print,version,buildInfo,
  getJSHeapLimitMB` + ES builtins + BSON types (`BinData,Code,ObjectId,MongoURI,...`) +
  `assert,tojson,ISODate`. **No** `cat/load/read/require/process/fs/Mongo/runProgram/importScripts`.
  `new Function('return process')()` -> ReferenceError. `import('fs')` returns a Promise that
  never resolves (no microtask drain in `$function`). `$where` exceptions ARE returned to the
  client (exfil channel) but there's nothing to exfil. Confirmed `security.javascriptEnabled`
  is on (SSJS runs) — deliberate, but leads nowhere for file read.
- **500 handler** ("Something went wrong!", text/plain) leaks nothing (NODE_ENV=production ->
  Bun `development:false`, no stack).

## Suspicious / unexplained (leads)
- Content sanitizer strips exactly `"`, `'`, `` ` `` — the 3 JS string delimiters. Implies
  the file content is meant to be evaluated as **JavaScript** somewhere, with `FLAG` inserted
  as a bare (unquoted) token. Where? mongod SSJS can't `load()` a file. `mongosh` `load()` is
  client-side. Restart-triggered `~/.mongoshrc.js` is unwritable (regex bans leading `.` and
  it's `/root` not `/tmp`). **Unresolved.**
- Filename regex specifically bans `-` (blocks `mongodb-27017.sock`), `_` (`node_modules`),
  and leading `.` (`.env`, `.bunfig.toml`, `.mongoshrc.js`). Reads like a denylist of
  "dangerous to create" names — but the write target is `/tmp`, where none of these are
  loaded from at runtime (CWD is `/`, config is baked into the compiled binary).
- Does a Bun `--compile` binary read `bunfig.toml` / `.env` from CWD at runtime? If CWD were
  `/tmp` this could give `preload` RCE — but startup-only, and CWD looks like `/`.
- `bun install --forzen-lockfile` (typo in Dockerfile) — build still succeeded.

## Next ideas to try
- Confirm app CWD (via a Bun behavior or an error).
- Bun 1.3.14 `Bun.serve` / `req.formData` / `Bun.write` known bugs (symlink follow on
  `Bun.write`? `createPath` default true?).
- Container restart behavior + whether anything reads `/tmp` on 2nd boot.
- Whether `Bun.write` follows a pre-existing symlink / dangling symlink in `/tmp`.
