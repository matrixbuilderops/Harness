def fast_split(data, pre_token_count):
    """
    Splits preamble tokens or metadata from data block.
    Returns a tuple (preamble, main_content).
    """
    return data[:pre_token_count], data[pre_token_count:]

def chunk_blocks(data, block_size):
    """
    Chunks main content into blocks of block_size.
    Returns a list of chunks.
    """
    return [data[i:i+block_size] for i in range(0, len(data), block_size)]

def final_trim(chunks, post_token_count):
    """
    Ensures no chunk exceeds post_token_count at tail.
    Trims post_token_count tokens from the end of each chunk if needed.
    """
    return [chunk[:-post_token_count] if len(chunk) > post_token_count else chunk for chunk in chunks]

def batch_chunks(chunks, batch_size):
    """
    Groups a list of chunks into batches of batch_size.
    Returns a list of lists (batches). The final batch may be smaller.
    
    Example:
        chunks = [1,2,3,4,5], batch_size=2
        output = [[1,2],[3,4],[5]]
    """
    return [chunks[i:i+batch_size] for i in range(0, len(chunks), batch_size)]