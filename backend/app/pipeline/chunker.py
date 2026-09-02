from typing import List, Dict, Any

def create_chunks(
    text: str,
    chunk_size: int = 500,
    overlap: int = 100
) -> List[Dict[str, Any]]:
    """
    Splits text into overlapping chunks while trying to preserve sentence/word boundaries.
    Returns a list of dicts containing chunk_index, text, start_char, end_char.
    """
    if not text:
        return []
    
    chunks = []
    start = 0
    text_len = len(text)
    chunk_idx = 0
    
    while start < text_len:
        end = start + chunk_size
        
        if end >= text_len:
            # Reached end of text
            chunk_text = text[start:text_len].strip()
            if chunk_text:
                chunks.append({
                    "chunk_index": chunk_idx,
                    "text": chunk_text,
                    "start_char": start,
                    "end_char": text_len
                })
            break
        
        # Look for a sentence boundary (., !, ?) or newline near the target end
        best_break = -1
        for punct in ['\n\n', '.\n', '. ', '!\n', '! ', '?\n', '? ', '\n']:
            pos = text.rfind(punct, start + int(chunk_size * 0.7), end)
            if pos != -1:
                best_break = pos + len(punct)
                break
        
        if best_break != -1:
            end = best_break
        else:
            # Fallback to word boundary
            space_pos = text.rfind(' ', start + int(chunk_size * 0.7), end)
            if space_pos != -1:
                end = space_pos + 1
        
        chunk_text = text[start:end].strip()
        if chunk_text:
            chunks.append({
                "chunk_index": chunk_idx,
                "text": chunk_text,
                "start_char": start,
                "end_char": end
            })
            chunk_idx += 1
            
        # Step forward by chunk_size - overlap
        step = max(1, (end - start) - overlap)
        start = start + step

    return chunks
