MIN_LENGTH = 4
MAX_LENGTH = 16

LATIN_EXTENDED_ADDITIONAL = range(0x1E00, 0x1F00)


def in_repertoire(character: str) -> bool:
    return "A" <= character <= "Z" or ord(character) in LATIN_EXTENDED_ADDITIONAL


def is_acceptable(name: str) -> bool:
    return (
        MIN_LENGTH <= len(name) <= MAX_LENGTH
        and all(in_repertoire(character) for character in name)
        and name.isalpha()
        and name.isupper()
    )
