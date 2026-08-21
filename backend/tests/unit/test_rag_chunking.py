import pytest

from backend.app.rag.chunking import (
    chunk_text,
)


def test_short_text_returns_single_chunk():
    chunks = chunk_text(
        "Refunds are available within 30 days.",
        chunk_size_words=10,
        overlap_words=2,
    )

    assert chunks == [
        "Refunds are available within 30 days."
    ]


def test_long_text_creates_overlapping_chunks():
    text = " ".join(
        f"word{i}"
        for i in range(12)
    )

    chunks = chunk_text(
        text,
        chunk_size_words=5,
        overlap_words=2,
    )

    assert chunks == [
        "word0 word1 word2 word3 word4",
        "word3 word4 word5 word6 word7",
        "word6 word7 word8 word9 word10",
        "word9 word10 word11",
    ]


def test_empty_text_is_rejected():
    with pytest.raises(
            ValueError,
            match="must not be empty",
    ):
        chunk_text(
            "   "
        )


def test_invalid_overlap_is_rejected():
    with pytest.raises(
            ValueError,
            match="overlap_words",
    ):
        chunk_text(
            "some knowledge",
            chunk_size_words=5,
            overlap_words=5,
        )