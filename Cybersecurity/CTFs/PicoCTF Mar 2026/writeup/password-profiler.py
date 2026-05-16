from pathlib import Path
#!/usr/bin/env python3
import hashlib

BASE_DIR = Path(__file__).resolve().parent
HASH_FILE = BASE_DIR / "hash.txt"
USERINFO_FILE = BASE_DIR / "userinfo.txt"


def parse_userinfo(path: str) -> dict[str, str]:
    data: dict[str, str] = {}
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            if ":" not in line:
                continue
            key, value = line.strip().split(":", 1)
            data[key.strip().lower()] = value.strip()
    return data


def normalize_birthdate(date_str: str) -> str:
    # userinfo uses DD-MM-YYYY, CUPP expects DDMMYYYY
    return date_str.replace("-", "")


def uniq(seq):
    return list(dict.fromkeys(seq))


def komb(seq, suffixes, special=""):
    for left in seq:
        for right in suffixes:
            yield left + special + right


def build_birthday_combos(birthdate: str) -> list[str]:
    parts = [
        birthdate[-2:],   # yy
        birthdate[-3:],   # yyy
        birthdate[-4:],   # yyyy
        birthdate[1:2],   # xd
        birthdate[3:4],   # xm
        birthdate[:2],    # dd
        birthdate[2:4],   # mm
    ]

    combos: list[str] = []
    for p1 in parts:
        combos.append(p1)
        for p2 in parts:
            if parts.index(p1) != parts.index(p2):
                combos.append(p1 + p2)
                for p3 in parts:
                    if (
                        parts.index(p1) != parts.index(p2)
                        and parts.index(p2) != parts.index(p3)
                        and parts.index(p1) != parts.index(p3)
                    ):
                        combos.append(p1 + p2 + p3)
    return combos


def build_name_combos(items: list[str]) -> list[str]:
    combos: list[str] = []
    for a in items:
        combos.append(a)
        for b in items:
            if items.index(a) != items.index(b) and items.index(a.title()) != items.index(b.title()):
                combos.append(a + b)
    return combos


def generate_candidates(info: dict[str, str]):
    name = info.get("first name", "").lower()
    surname = info.get("surname", "").lower()
    nick = info.get("nickname", "").lower()
    partner = info.get("partner's name", "").lower()
    child = info.get("child's name", "").lower()
    birthdate = normalize_birthdate(info.get("birthdate", ""))

    nameup = name.title()
    surnameup = surname.title()
    nickup = nick.title()
    partnerup = partner.title()
    childup = child.title()

    rev_name = name[::-1]
    rev_nameup = nameup[::-1]
    rev_nick = nick[::-1]
    rev_nickup = nickup[::-1]
    rev_partner = partner[::-1]
    rev_partnerup = partnerup[::-1]
    rev_child = child[::-1]
    rev_childup = childup[::-1]

    reverse = [
        rev_name,
        rev_nameup,
        rev_nick,
        rev_nickup,
        rev_partner,
        rev_partnerup,
        rev_child,
        rev_childup,
    ]

    bdss = build_birthday_combos(birthdate)

    kombina = [name, surname, nick, nameup, surnameup, nickup]
    kombinaa = build_name_combos(kombina)

    # CUPP also uses a years list, but we do not need it for this challenge.
    # The target password is generated from the name profile + birthday combos.
    candidates = []
    candidates += bdss
    candidates += reverse
    candidates += uniq(kombinaa)
    candidates += list(komb(kombinaa, bdss))
    candidates += list(komb(kombinaa, bdss, "_"))

    # Keep the same length filter CUPP applies by default.
    for candidate in uniq(candidates):
        if 5 < len(candidate) < 12:
            yield candidate



def crack_password(target_hash: str, info: dict[str, str]) -> str | None:
    for candidate in generate_candidates(info):
        if hashlib.sha1(candidate.encode()).hexdigest() == target_hash:
            return candidate
    return None


if __name__ == "__main__":
    with open(HASH_FILE, "r", encoding="utf-8") as f:
        target_hash = f.read().strip()

    info = parse_userinfo(USERINFO_FILE)
    password = crack_password(target_hash, info)

    if password is None:
        print("No match found.")
    else:
        print(f"Password found: picoCTF{{{password}}}")
