def chunk_text(
        text: str,
        *,
        chunk_size_words: int = 180,
        overlap_words: int = 30,
) -> list[str]:
    cleaned_text = " ".join(
        text.split()
    )

    if not cleaned_text:
        raise ValueError(
            "Knowledge document content "
            "must not be empty"
        )

    if chunk_size_words <= 0:
        raise ValueError(
            "chunk_size_words must be positive"
        )

    if overlap_words < 0:
        raise ValueError(
            "overlap_words must not be negative"
        )

    if overlap_words >= chunk_size_words:
        raise ValueError(
            "overlap_words must be smaller "
            "than chunk_size_words"
        )

    words = cleaned_text.split()

    if len(words) <= chunk_size_words:
        return [cleaned_text]

    chunks: list[str] = []

    step = (
            chunk_size_words
            - overlap_words
    )

    start = 0

    while start < len(words):
        end = min(
            start + chunk_size_words,
            len(words),
            )

        chunk = " ".join(
            words[start:end]
        )

        chunks.append(chunk)

        if end == len(words):
            break

        start += step

    return chunks