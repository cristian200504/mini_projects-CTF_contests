# file-monster — progress notes (not solved yet)

## What the challenge is

A Bun web app running inside the `mongo:8.2.10` image. Two things are exposed:

- the web interface (Bun, port 3000)
- MongoDB itself over TLS, with a read-only user `viewer:viewer` on the
  `file-monster` database

The whole app is `src/index.ts` (89 lines). It:

- serves `/` (a static HTML page) and `/robots.txt` (a static Response built once
  at startup from an embedded file)
- `POST /upload`: takes a multipart `file`. The filename must match
  `^[a-zA-Z][a-zA-Z0-9.]*$` (letters, digits and dots only, must start with a
  letter). If `/tmp/<filename>` already exists it returns
  "Filename is already in use". Otherwise it takes the uploaded text, deletes
  every `"`, `'` and `` ` `` from it, replaces the first occurrence of the
  literal string `FLAG` with `process.env.FLAG`, and writes the result to
  `/tmp/<filename>`. It then stores `{ name: <filename> }` in the `files`
  collection in Mongo.
- `GET /files`: dumps every document in `files` — but the schema only has a
  `name` field, so you only get back the list of filenames, nothing else.

The app connects to Mongo as the **admin** user over a unix socket at
`/tmp/mongodb-27017.sock`.

So the flag only ever ends up in two places: the environment variable
`process.env.FLAG`, and the body of whatever `/tmp/<name>` file you uploaded a
`FLAG` marker into. Nothing in the app reads those files back or echoes the
environment, so the whole challenge is: find a way to read `/tmp/<yourfile>` (or
`/proc/<pid>/environ`).

## What I confirmed against the live instance

**The filename filter cannot be bypassed.** I threw a lot at it: `../`, `..\`,
URL-encoded `%2e%2e%2f`, the RFC 5987 `filename*=UTF-8''...` form (Bun ignores it
entirely), MIME quoted-pair escapes like `"a\/b"`, raw CR / LF / NUL / tab /
control bytes in the filename, header folding, duplicate `Content-Disposition`
headers, duplicate `filename=` parameters, unquoted values, a trailing newline
(JavaScript's `$` is an absolute end-of-string anchor with no `m` flag, so it
rejects `"abc\n"`), overlong UTF-8, etc. In every case either the regex rejects
it or Bun's parser normalises it. The response always echoes back
`path: /tmp/<exact-name>`, and re-uploading the same name always says "already in
use", so the write really does land exactly where the name says — no
check-here-write-there trick. One curiosity: sending `filename=""` makes Bun
report the name as the literal string `"undefined"`.

**There is no way to read `/tmp` over HTTP.** Only four routes exist
(`/`, `/robots.txt`, `/upload`, `/files`) plus the two auto-generated asset
chunks for the HTML page. Every path I guessed 404s. Directory-traversal attempts
on the chunk URLs and on `/robots.txt` all 404. Uploading files named
`robots.txt` or `index.html` does not change what those routes serve, because the
`Response` / HTML bundle objects are built once at startup from the compiled
binary's embedded filesystem, not from disk.

**`/tmp` is a normal empty directory.** It is not a symlink to `/`. Using the
"already in use" response as an existence oracle, names like `etc`, `bin`, `usr`,
`data`, `WiredTiger`, `mongod.lock`, `storage.bson` all come back as new, so
neither `/` nor Mongo's data directory (`/data/db`) lives under `/tmp`. The only
real occupant of `/tmp` is the Mongo socket `mongodb-27017.sock`, and its name
contains a hyphen, which the filename regex forbids — so I can't create or
shadow it.

**The MongoDB `viewer` user is a dead end for reading the flag.** It has the
plain `read` role on `file-monster` and nothing else. It can `find` / `aggregate`
on the `files` collection (names only) and run server-side JavaScript via
`$where` / `$function` / `mapReduce`. Everything else is denied: no
`serverStatus`, `hostInfo`, `getCmdLineOpts`, `getLog`, `getParameter` (any
parameter), `validate`, no access to the `admin` / `local` / `config` databases,
no writes of any kind, no `$currentOp` for other users, no cross-database
`$lookup` / `$unionWith`. It is a standalone server (not a replica set) so change
streams don't work. There is no weak admin password, and connecting with no
credentials gets you nothing.

**MongoDB server-side JavaScript is fully sandboxed.** In `$where` / `$function`
the global scope is only `Function, Object, eval, sleep, gc, print, version,
buildInfo, getJSHeapLimitMB`, the normal ECMAScript built-ins, and the BSON
helper types (`BinData`, `Code`, `ObjectId`, `MongoURI`, `assert`, `tojson`,
`ISODate`, …). There is **no** `cat`, `load`, `read`, `require`, `process`,
`fs`, `Mongo` or `runProgram`. `new Function('return process')()` throws a
ReferenceError. `import('fs')` returns a Promise that never settles because
`$function` runs synchronously and never drains the microtask queue. So Mongo's
JS engine cannot touch the filesystem, the environment, or the logs, and there
is no visible sandbox escape. (The config file deliberately leaves server-side
JS enabled, which feels like a hint, but I could not find where it leads.)

**The 500 error page leaks nothing** — it's a fixed "Something went wrong!" with
no stack trace, because `NODE_ENV=production` makes Bun disable development-mode
error output.

## The thing I can't place

The upload handler strips exactly the three JavaScript string delimiters
(`"`, `'`, `` ` ``). That strongly suggests the uploaded file is meant to be
executed as JavaScript somewhere, with the flag pasted in as a bare, unquoted
token — a classic "inject JS but you have no way to make a string literal"
setup. But:

- Mongo's server-side JS cannot `load()` a file.
- `mongosh`'s `load()` runs on the client, i.e. on my machine, not the server.
- `~/.mongoshrc.js` would be run by the `mongosh` call in `entrypoint.sh`, but
  that path is `/root/...` (the regex forbids a leading dot and only lets me
  write under `/tmp`), and it only runs at container start, before the app is up.
- The challenge description has no "admin bot" / checker section, so there is
  probably no process that eats and executes the files you upload.

The filename regex also specifically bans `-` (which blocks recreating
`mongodb-27017.sock`), `_` (blocks `node_modules`), and a leading dot (blocks
`.env`, `.bunfig.toml`, `.mongoshrc.js`) — it reads like a denylist of
"dangerous filenames", but the write target is `/tmp`, and Bun doesn't load any
of those from `/tmp` at runtime (the app's working directory looks like `/`, and
the config is baked into the `--compile`d binary).

## Where I got to

I could not find the read primitive purely by black-box testing plus reading the
handout source. My best guesses for the intended path, still unverified:

- some Bun 1.3.14 quirk in `Bun.serve` static handling, `req.formData()`, or
  `Bun.write` (e.g. following a symlink, or `createPath` behaviour)
- the app's working directory actually being somewhere writable, plus a Bun
  compiled-binary config file being read at runtime, plus a container restart
- a consumer/checker process (the "file monster") that runs uploaded files,
  which isn't in the handout

Next step is to build and run the challenge locally in Docker so the running
container can be inspected directly — working directory of the backend process,
its full environment, the contents of `/tmp`, the process list, and whether
anything periodically consumes `/tmp`.
