import os
import re
from deep_translator import GoogleTranslator

translator = GoogleTranslator(source='auto', target='it')  # Target language set to Italian

def protect_special_content(text):
    # Protect dynamic keys like {{ variable }}
    dynamic_key_pattern = re.compile(r'{{.*?}}')
    dynamic_keys = dynamic_key_pattern.findall(text)
    for i, key in enumerate(dynamic_keys):
        text = text.replace(key, f"__DYNAMIC_KEY_{i}__")

    # Protect HTML tags like <p>, <h1>, etc.
    html_tag_pattern = re.compile(r'<.*?>')
    html_tags = html_tag_pattern.findall(text)
    for i, tag in enumerate(html_tags):
        text = text.replace(tag, f"__HTML_TAG_{i}__")

    return text, dynamic_keys, html_tags

def restore_special_content(text, dynamic_keys, html_tags):
    # Restore dynamic keys
    for i, key in enumerate(dynamic_keys):
        text = text.replace(f"__DYNAMIC_KEY_{i}__", key)
    # Restore HTML tags
    for i, tag in enumerate(html_tags):
        text = text.replace(f"__HTML_TAG_{i}__", tag)

    return text

# Ensure that the last characters are safe to split (not inside HTML tags or variables)
def is_safe_to_split(text):
    # Don't split if the text ends inside an unclosed HTML tag or dynamic variable
    if re.search(r'{{[^}}]*$|<[^>]*$', text):
        return False
    return True

# Function to split text into safe chunks, enforcing a strict 4000-character limit
def split_text_safely(text, base_length=4000, max_length=4000):
    """Splits text into chunks that do not exceed 4000 characters and preserves spaces."""
    words = text.split(' ')
    chunks = []
    current_chunk = ""

    for word in words:
        if len(current_chunk) + len(word) + 1 > base_length:  # +1 for space
            # Ensure the chunk is safe to split and doesn't break HTML tags or variables
            while not is_safe_to_split(current_chunk) and len(current_chunk) < max_length:
                current_chunk += " " + word
                word = next(iter(words), "")

            # Add the safely formed chunk and reset the current chunk
            chunks.append(current_chunk.strip())
            current_chunk = word
        else:
            if current_chunk:
                current_chunk += " "  # Add space between words
            current_chunk += word

    if current_chunk.strip():
        chunks.append(current_chunk.strip())

    return chunks

def translate_large_string(text):
    protected_text, dynamic_keys, html_tags = protect_special_content(text)

    # Split the text into safe chunks (max 4000 characters per chunk)
    chunks = split_text_safely(protected_text)
    translated_chunks = [translator.translate(chunk) for chunk in chunks]

    # Reassemble the translated chunks, ensuring no extra spaces
    translated_text = "".join(translated_chunks)

    # Restore dynamic keys and HTML tags in the final translated text
    final_text = restore_special_content(translated_text, dynamic_keys, html_tags)
    
    return final_text

def translate_text_between_html_tags(text):
    """Translates only the text between HTML tags, while leaving the tags and variables intact."""
    # Protect dynamic keys and HTML tags
    protected_text, dynamic_keys, html_tags = protect_special_content(text)

    # Translate only the text between HTML tags, preserving the tags and variables
    def translate_match(match):
        return f">{translator.translate(match.group(1))}<"

    # Find text between HTML tags and translate
    translated_text = re.sub(r'>([^<]+)<', lambda m: translate_match(m), protected_text)

    # Restore dynamic keys and HTML tags
    final_text = restore_special_content(translated_text, dynamic_keys, html_tags)
    
    return final_text

def translate_string_value(data):
    if len(data) > 4000:
        return translate_large_string(data)
    else:
        return translate_text_between_html_tags(data)

def process_and_translate_file(file_path, output_folder):
    with open(file_path, 'r', encoding='utf-8') as string_file:
        data = string_file.read()

    translated_data = translate_string_value(data)
    
    os.makedirs(output_folder, exist_ok=True)
    file_name = os.path.basename(file_path)
    translated_file_path = os.path.join(output_folder, file_name)

    with open(translated_file_path, 'w', encoding='utf-8') as output_file:
        output_file.write(translated_data)

    print(f"Translated file saved to: {translated_file_path}")

if __name__ == "__main__":
    input_folder_path = "./strings"  # Folder with the original strings
    output_folder_path = "./it_strings"  # Folder for translated files

    for file_name in os.listdir(input_folder_path):
        if file_name.endswith('.txt'):  # Assuming the string content is in .txt files
            input_file_path = os.path.join(input_folder_path, file_name)
            output_file_path = os.path.join(output_folder_path, file_name)
            if os.path.exists(output_file_path):
                print(f"Skipping {file_name}, already translated.")
            else:
                process_and_translate_file(input_file_path, output_folder_path)
