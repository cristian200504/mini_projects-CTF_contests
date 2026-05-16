#!/usr/bin/env python3
"""
Whisper APK CTF cracker

What it does:
- Connects to a Socket.IO server (host:port)
- Listens for the `session_bundle` event
- Computes the expected auth token: HMAC-SHA256(key, session_id).hexdigest()
- Decrypts the encrypted payload: bytes.fromhex(encrypted) XOR key[i % 32]
- Tries to extract an access token / URL from decrypted plaintext (JSON or raw string)
- Optionally calls a control/relay HTTP endpoint with the token to retrieve a flag

Dependencies:
  pip install "python-socketio[client]" requests
"""

from __future__ import annotations

import argparse
import hmac
import hashlib
import json
import sys
import time
from dataclasses import dataclass
from typing import Any, Optional, Dict, List, Tuple

import requests
import socketio


KEY = b"NobodyExpectsTheSpainishInquisit"  # 32 bytes, exact spelling


@dataclass
class SessionBundle:
    encrypted_hex: str
    length: Optional[int]
    session_id: Optional[str]
    auth_token: Optional[str]
    raw: Dict[str, Any]


def compute_auth_token(session_id: str, key: bytes = KEY) -> str:
    """Compute auth_token = HMAC-SHA256(key, session_id).hexdigest()"""
    return hmac.new(key, session_id.encode("utf-8"), hashlib.sha256).hexdigest()


def decrypt_session_bundle(encrypted_hex: str, length: Optional[int], key: bytes = KEY) -> bytes:
    """
    Decrypts the encrypted blob.
    Native behavior (from libwhisper_crypto.so) is effectively:
      plaintext[i] = decoded_bytes[i] XOR key[i % 32]
    and then truncate to `length` bytes (if length provided).
    """
    hx = encrypted_hex.strip()
    # tolerate "0x..." or whitespace/newlines
    if hx.startswith("0x") or hx.startswith("0X"):
        hx = hx[2:]
    hx = "".join(hx.split())

    if len(hx) % 2 != 0:
        raise ValueError("encrypted hex has odd length (not valid hex bytes)")

    data = bytes.fromhex(hx)
    out = bytes((b ^ key[i % len(key)]) for i, b in enumerate(data))
    if length is not None:
        out = out[: max(0, int(length))]
    return out


def try_parse_decrypted(decrypted: bytes) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """
    Try to interpret decrypted bytes as:
      1) JSON object (preferred)
      2) raw token string
    Returns: (json_obj, raw_text)
    """
    # try utf-8, fall back to latin1 for visibility
    text = None
    try:
        text = decrypted.decode("utf-8", errors="strict")
    except UnicodeDecodeError:
        text = decrypted.decode("latin1", errors="replace")

    text_stripped = text.strip("\x00\r\n\t ")

    # JSON?
    try:
        obj = json.loads(text_stripped)
        if isinstance(obj, dict):
            return obj, text_stripped
    except Exception:
        pass

    return None, text_stripped if text_stripped else None


def extract_candidate_tokens(obj: Optional[Dict[str, Any]], raw_text: Optional[str]) -> Dict[str, str]:
    """
    Pull out likely tokens/urls from decrypted content.
    If JSON, look for common fields. If not, treat raw_text as token-ish.
    """
    candidates: Dict[str, str] = {}

    if obj:
        # common keys in CTFs / APIs
        for k in (
            "access_token", "token", "bearer", "auth", "auth_token",
            "api_key", "apikey", "key", "session_token"
        ):
            v = obj.get(k)
            if isinstance(v, str) and v.strip():
                candidates[f"json:{k}"] = v.strip()

        # common URL keys
        for k in ("url", "endpoint", "relay", "control_url", "api_url", "base_url"):
            v = obj.get(k)
            if isinstance(v, str) and v.strip():
                candidates[f"json:{k}"] = v.strip()

    if raw_text:
        # If it looks like a URL or a long token, keep it.
        rt = raw_text.strip()
        if rt.startswith("http://") or rt.startswith("https://"):
            candidates["raw:url"] = rt
        # heuristic: tokens are often fairly long, no spaces
        if " " not in rt and len(rt) >= 16:
            candidates["raw:tokenish"] = rt

    return candidates


def call_control_api(
    base_url: str,
    token: str,
    endpoint_path: str,
    header_mode: str = "authorization_bearer",
    timeout: float = 10.0,
    verify_tls: bool = True,
) -> requests.Response:
    """
    Make an HTTP request to retrieve the flag (or whatever the API returns).
    header_mode:
      - authorization_bearer: Authorization: Bearer <token>
      - authorization_raw:    Authorization: <token>
      - x_auth_token:         X-Auth-Token: <token>
      - query_token:          ?token=<token>
    """
    if not base_url.startswith(("http://", "https://")):
        base_url = "http://" + base_url

    if not endpoint_path.startswith("/"):
        endpoint_path = "/" + endpoint_path

    headers = {}
    url = base_url.rstrip("/") + endpoint_path

    if header_mode == "authorization_bearer":
        headers["Authorization"] = f"Bearer {token}"
    elif header_mode == "authorization_raw":
        headers["Authorization"] = token
    elif header_mode == "x_auth_token":
        headers["X-Auth-Token"] = token
    elif header_mode == "query_token":
        # attach as query parameter
        joiner = "&" if "?" in url else "?"
        url = f"{url}{joiner}token={requests.utils.quote(token)}"
    else:
        raise ValueError(f"Unknown header_mode: {header_mode}")

    # Try GET first (most CTF flags are returned via GET)
    resp = requests.get(url, headers=headers, timeout=timeout, verify=verify_tls)
    return resp


def wait_for_session_bundle(
    host: str,
    port: int,
    use_https: bool = False,
    namespace: Optional[str] = None,
    timeout_sec: float = 20.0,
    verbose: bool = True,
) -> SessionBundle:
    """
    Connect to Socket.IO server and wait for `session_bundle`.
    """
    scheme = "https" if use_https else "http"
    base = f"{scheme}://{host}:{port}"

    sio = socketio.Client(
        reconnection=False,
        logger=verbose,
        engineio_logger=verbose,
    )

    captured: Dict[str, Any] = {}
    got = {"ok": False}

    @sio.event(namespace=namespace)
    def connect():
        if verbose:
            print(f"[+] Connected to {base} (namespace={namespace or '/'})")

    @sio.event(namespace=namespace)
    def connect_error(data):
        raise RuntimeError(f"Socket.IO connect_error: {data!r}")

    @sio.event(namespace=namespace)
    def disconnect():
        if verbose:
            print("[*] Disconnected.")

    @sio.on("session_bundle", namespace=namespace)
    def on_session_bundle(data):
        if verbose:
            print("[+] Received session_bundle!")
        captured["data"] = data
        got["ok"] = True
        sio.disconnect()

    if verbose:
        print(f"[*] Connecting to Socket.IO: {base}")

    # Many servers support both polling+websocket; allow default behavior.
    # If it fails in your environment, try transports=['polling'].
    sio.connect(base, namespaces=[namespace] if namespace else None)

    t0 = time.time()
    while time.time() - t0 < timeout_sec:
        if got["ok"]:
            break
        sio.sleep(0.1)

    if not got["ok"]:
        try:
            sio.disconnect()
        except Exception:
            pass
        raise TimeoutError("Timed out waiting for `session_bundle` event.")

    data = captured["data"]
    if not isinstance(data, dict):
        raise ValueError(f"Unexpected session_bundle payload type: {type(data)}")

    # expected fields from the APK’s logic
    encrypted_hex = str(data.get("encrypted", ""))
    length = data.get("length")
    session_id = data.get("session_id")
    auth_token = data.get("auth_token")

    if encrypted_hex == "":
        raise ValueError("session_bundle did not contain `encrypted`")

    return SessionBundle(
        encrypted_hex=encrypted_hex,
        length=int(length) if isinstance(length, (int, float, str)) and str(length).isdigit() else None,
        session_id=str(session_id) if session_id is not None else None,
        auth_token=str(auth_token) if auth_token is not None else None,
        raw=data,
    )


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Crack Whisper APK CTF: capture session_bundle, decrypt, compute token, call control endpoint."
    )
    ap.add_argument("--host", required=True, help="Socket.IO host / IP")
    ap.add_argument("--port", required=True, type=int, help="Socket.IO port")
    ap.add_argument("--https", action="store_true", help="Use https:// for socket connection")

    ap.add_argument("--namespace", default=None, help="Socket.IO namespace (rare; default is /)")

    ap.add_argument("--offline-bundle", help="Path to a JSON file containing the session_bundle payload (skip socket connect)")
    ap.add_argument("--timeout", type=float, default=20.0, help="Seconds to wait for session_bundle")

    ap.add_argument("--dump", action="store_true", help="Print full raw session_bundle JSON")
    ap.add_argument("--save-decrypted", help="Write decrypted bytes to this file")

    # control API / relay fetch
    ap.add_argument("--control-base", help="Base URL for control API (default: same as socket host:port)")
    ap.add_argument("--control-path", help="HTTP path to request for flag, e.g. /control/flag or /relay")
    ap.add_argument(
        "--header-mode",
        default="authorization_bearer",
        choices=["authorization_bearer", "authorization_raw", "x_auth_token", "query_token"],
        help="How to send the token to the control API",
    )
    ap.add_argument("--no-verify-tls", action="store_true", help="Disable TLS verification for HTTPS calls")
    ap.add_argument("--auto-try-paths", action="store_true",
                    help="If --control-path not set, try a small list of common CTF paths.")
    ap.add_argument("--verbose", action="store_true", help="Verbose Socket.IO logs")

    args = ap.parse_args()

    # --- acquire bundle
    if args.offline_bundle:
        with open(args.offline_bundle, "r", encoding="utf-8") as f:
            data = json.load(f)
        sb = SessionBundle(
            encrypted_hex=str(data.get("encrypted", "")),
            length=int(data["length"]) if "length" in data and str(data["length"]).isdigit() else None,
            session_id=str(data.get("session_id")) if data.get("session_id") is not None else None,
            auth_token=str(data.get("auth_token")) if data.get("auth_token") is not None else None,
            raw=data,
        )
        if not sb.encrypted_hex:
            print("[-] offline bundle JSON missing `encrypted`")
            return 2
    else:
        sb = wait_for_session_bundle(
            host=args.host,
            port=args.port,
            use_https=args.https,
            namespace=args.namespace,
            timeout_sec=args.timeout,
            verbose=args.verbose,
        )

    if args.dump:
        print("\n==== Raw session_bundle ====")
        print(json.dumps(sb.raw, indent=2, sort_keys=True))

    # --- compute expected auth token
    expected = None
    if sb.session_id:
        expected = compute_auth_token(sb.session_id)
        print(f"\n[+] session_id: {sb.session_id}")
        print(f"[+] expected auth_token (HMAC-SHA256): {expected}")
        if sb.auth_token:
            ok = (sb.auth_token.strip().lower() == expected.lower())
            print(f"[+] server auth_token: {sb.auth_token}")
            print(f"[+] auth_token match? {'YES' if ok else 'NO'}")
        else:
            print("[*] server did not provide auth_token field (or it was null)")
    else:
        print("[*] No session_id provided in bundle; skipping HMAC check.")

    # --- decrypt blob
    try:
        dec = decrypt_session_bundle(sb.encrypted_hex, sb.length)
    except Exception as e:
        print(f"[-] decrypt failed: {e}")
        return 3

    print("\n==== Decrypted session bundle (best-effort text) ====")
    try:
        print(dec.decode("utf-8", errors="replace"))
    except Exception:
        print(repr(dec))

    if args.save_decrypted:
        with open(args.save_decrypted, "wb") as f:
            f.write(dec)
        print(f"[+] wrote decrypted bytes to: {args.save_decrypted}")

    obj, raw_text = try_parse_decrypted(dec)
    candidates = extract_candidate_tokens(obj, raw_text)

    if obj:
        print("\n[+] Decrypted JSON keys:", ", ".join(sorted(obj.keys())))
    if candidates:
        print("\n[+] Candidate values extracted from decrypted content:")
        for k, v in candidates.items():
            print(f"    - {k}: {v}")
    else:
        print("\n[*] No obvious token/url fields found in decrypted content. It may just be raw text above.")

    # Choose a token to try against control API:
    # Prefer a decrypted token-like value; otherwise fall back to expected HMAC token.
    chosen_token = None
    for pref in ("json:access_token", "json:token", "json:auth_token", "raw:tokenish"):
        if pref in candidates:
            chosen_token = candidates[pref]
            break
    if chosen_token is None and expected:
        chosen_token = expected

    if not chosen_token:
        print("\n[-] No token available to call control API (no decrypted token, no session_id-derived token).")
        return 0

    # --- optional control API call
    control_base = args.control_base or f"{'https' if args.https else 'http'}://{args.host}:{args.port}"
    verify_tls = not args.no_verify_tls

    paths_to_try: List[str] = []
    if args.control_path:
        paths_to_try = [args.control_path]
    elif args.auto_try_paths:
        # Keep this small and non-destructive (GET only).
        paths_to_try = [
            "/flag",
            "/control",
            "/control/flag",
            "/relay",
            "/relay/flag",
            "/api/flag",
            "/api/control",
            "/v1/flag",
        ]

    if paths_to_try:
        print(f"\n[*] Trying control API with token ({args.header_mode}) against base: {control_base}")
        for p in paths_to_try:
            try:
                resp = call_control_api(
                    base_url=control_base,
                    token=chosen_token,
                    endpoint_path=p,
                    header_mode=args.header_mode,
                    verify_tls=verify_tls,
                )
                print(f"\n=== GET {p} -> HTTP {resp.status_code} ===")
                # print body (CTF flags are usually in plaintext/JSON)
                ct = resp.headers.get("Content-Type", "")
                if "application/json" in ct:
                    try:
                        print(json.dumps(resp.json(), indent=2))
                    except Exception:
                        print(resp.text)
                else:
                    print(resp.text)
                # Stop early if it looks like a flag
                if "flag" in resp.text.lower() or "ctf" in resp.text.lower():
                    print("[+] Looks like we got something flag-like; stopping.")
                    break
            except Exception as e:
                print(f"[-] Failed on path {p}: {e}")

    else:
        print("\n[*] Skipping control API call (no --control-path and no --auto-try-paths).")
        print(f"    Token you can use manually: {chosen_token}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())