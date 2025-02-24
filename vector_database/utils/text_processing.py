import tiktoken
import pandas as pd
from ..config import MAX_TOKENS

def clip_text_to_max_tokens(text, max_tokens, encoding_name='cl100k_base'):
    encoding = tiktoken.get_encoding(encoding_name)
    tokens = encoding.encode(text)
    original_token_count = len(tokens)
    
    print(f"\nOriginal text ({original_token_count} tokens):")
    print("=" * 50)
    print(text[:200] + "..." if len(text) > 200 else text)
    
    if original_token_count > max_tokens:
        tokens = tokens[:max_tokens]
        clipped_text = encoding.decode(tokens)
        print(f"\nClipped text ({len(tokens)} tokens):")
        print("=" * 50)
        print(clipped_text[:200] + "..." if len(clipped_text) > 200 else clipped_text)
        return clipped_text
    
    return text

def create_markdown_dataframe(markdown_contents):
    df = pd.DataFrame(list(markdown_contents.items()), columns=['file_path', 'source_code'])
    df['source_code'] = df.apply(
        lambda row: f"File: {row['file_path']}\n\nContent:\n{clip_text_to_max_tokens(row['source_code'], MAX_TOKENS)}\n\n",
        axis=1
    )
    
    for col in ['class_name', 'constructor_declaration', 'method_declarations', 'references']:
        df[col] = "empty"
    return df 