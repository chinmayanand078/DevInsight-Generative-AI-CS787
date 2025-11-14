def chunk_text(text: str, max_tokens: int = 250):
    """
    Splits text into semantic chunks based on paragraph boundaries.
    Ensures each chunk stays below max_tokens length for efficient embeddings.
    """
    paragraphs = text.split("\n\n")
    chunks = []
    current = ""

    for para in paragraphs:
        if len(current) + len(para) <= max_tokens:
            current += para + "\n\n"
        else:
            chunks.append(current.strip())
            current = para + "\n\n"

    if current.strip():
        chunks.append(current.strip())

    return chunks


