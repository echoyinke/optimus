def split_text(text, max_length=1000):
    start = 0
    split_texts = []
    while start < len(text):
        end = start + max_length
        if end < len(text):
            while end > start and text[end] not in (' ', '\n', '\t'):
                end -= 1
        if end == start:
            end = start + max_length
        split_texts.append(text[start:end])
        start = end
    return split_texts