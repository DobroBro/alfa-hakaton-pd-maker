def _is_letter(ch: str) -> bool:
    return ch.isalpha()


def has_keyword(folded: str, start: int, end: int, keywords: tuple[str, ...], window: int) -> bool:
    """Search keywords in folded[start-window:end+window].
    A match is not counted if there is a letter immediately left or right."""
    lo = max(0, start - window)
    hi = min(len(folded), end + window)
    region = folded[lo:hi]
    for kw in keywords:
        idx = region.find(kw)
        while idx != -1:
            abs_idx = lo + idx
            left_ok = abs_idx == 0 or not _is_letter(folded[abs_idx - 1])
            right_ok = abs_idx + len(kw) >= len(folded) or not _is_letter(
                folded[abs_idx + len(kw)]
            )
            if left_ok and right_ok:
                return True
            idx = region.find(kw, idx + 1)
    return False


def has_stop_context(folded: str, start: int, end: int, keywords: tuple[str, ...]) -> bool:
    """Same as has_keyword but window only to the left of start, length 60."""
    return has_keyword_left(folded, start, keywords, 60)


def has_keyword_left(folded: str, start: int, keywords: tuple[str, ...], window: int) -> bool:
    """Search keywords in folded[start-window:start]."""
    lo = max(0, start - window)
    region = folded[lo:start]
    for kw in keywords:
        idx = region.find(kw)
        while idx != -1:
            abs_idx = lo + idx
            left_ok = abs_idx == 0 or not _is_letter(folded[abs_idx - 1])
            right_ok = abs_idx + len(kw) >= start or not _is_letter(folded[abs_idx + len(kw)])
            if left_ok and right_ok:
                return True
            idx = region.find(kw, idx + 1)
    return False


def has_keyword_prefix(folded: str, start: int, end: int, keywords: tuple[str, ...], window: int) -> bool:
    """Search keywords in folded[start-window:end+window] as word prefixes (left boundary only)."""
    lo = max(0, start - window)
    hi = min(len(folded), end + window)
    region = folded[lo:hi]
    for kw in keywords:
        idx = region.find(kw)
        while idx != -1:
            abs_idx = lo + idx
            left_ok = abs_idx == 0 or not _is_letter(folded[abs_idx - 1])
            if left_ok:
                return True
            idx = region.find(kw, idx + 1)
    return False


def closest_key_end(folded: str, start: int, end: int, keywords: tuple[str, ...], window: int) -> int | None:
    """Return the end index of the keyword occurrence whose end is closest to `start`."""
    lo = max(0, start - window)
    hi = min(len(folded), end + window)
    region = folded[lo:hi]
    best = None
    best_dist = None
    for kw in keywords:
        idx = region.find(kw)
        while idx != -1:
            abs_idx = lo + idx
            left_ok = abs_idx == 0 or not _is_letter(folded[abs_idx - 1])
            right_ok = abs_idx + len(kw) >= len(folded) or not _is_letter(
                folded[abs_idx + len(kw)]
            )
            if left_ok and right_ok:
                key_end = abs_idx + len(kw)
                dist = abs(key_end - start)
                if best_dist is None or dist < best_dist:
                    best_dist = dist
                    best = key_end
            idx = region.find(kw, idx + 1)
    return best