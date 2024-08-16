def ref_split(ref: str) -> tuple[str, str]:
    for i, c in enumerate(ref):
        if c in "><^=":
            break
    else:
        i += 1

    return ref[:i], ref[i:]
