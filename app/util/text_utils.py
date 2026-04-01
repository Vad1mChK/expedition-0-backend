import re

WORD_REGEX = re.compile(r'\b(\d+(?:\.\d+)?|[0-9A-Za-zЁёА-Яа-я]+(?:-[0-9A-Za-zЁёА-Яа-я]+)*)\b')


def clear_text(text: str, to_lowercase: bool = False) -> str:
    if not text:
        return ""

    # findall returns a list of matched groups
    words = WORD_REGEX.findall(text)
    cleaned = ' '.join(words)

    return cleaned.lower() if to_lowercase else cleaned
