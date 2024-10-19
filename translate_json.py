import json
import os
import re
from deep_translator import GoogleTranslator

translator = GoogleTranslator(source='auto', target='en') # target = language you want to translate the files

def protect_special_content(text):
    # prevent dynamic keys to be translated
    dynamic_key_pattern = re.compile(r'{{.*?}}')
    dynamic_keys = dynamic_key_pattern.findall(text)
    for i, key in enumerate(dynamic_keys):
        text = text.replace(key, f"__DYNAMIC_KEY_{i}__")
    
    html_tag_pattern = re.compile(r'<.*?>')
    html_tags = html_tag_pattern.findall(text)
    for i, tag in enumerate(html_tags):
        text = text.replace(tag, f"__HTML_TAG_{i}__")

    return text, dynamic_keys, html_tags

def restore_special_content(text, dynamic_keys, html_tags):
    for i, key in enumerate(dynamic_keys):
        text = text.replace(f"__DYNAMIC_KEY_{i}__", key)
    for i, tag in enumerate(html_tags):
        text = text.replace(f"__HTML_TAG_{i}__", tag)

    return text

# ensure that the last characthers is safe to split and be replaced
def is_safe_to_split(text):
    last_10_chars = text[-10:] 
    if re.search(r'{{.*$|<.*$', last_10_chars):
        return False
    return True

# Function to split text into safe chunks with a base limit of 4000 characters, ensuring no tags or keys are broken
def split_text_safely(text, base_length=4000, max_length=5000):
    words = text.split(' ')
    chunks = []
    current_chunk = ""

    for word in words:
        if len(current_chunk) + len(word) + 1 > base_length:
            while not is_safe_to_split(current_chunk) and len(current_chunk) < max_length:
                current_chunk += word + " "
                word = next(iter(words), "")

            chunks.append(current_chunk.strip())
            current_chunk = word + " "
        else:
            current_chunk += word + " "

    if current_chunk.strip():
        chunks.append(current_chunk.strip())

    return chunks

def translate_large_string(text):
    protected_text, dynamic_keys, html_tags = protect_special_content(text)

    chunks = split_text_safely(protected_text)
    translated_chunks = [translator.translate(chunk) for chunk in chunks]

    translated_text = "".join(translated_chunks)

    final_text = restore_special_content(translated_text, dynamic_keys, html_tags)
    
    return final_text

def translate_json_values(data):
    if isinstance(data, dict):
        return {key: translate_json_values(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [translate_json_values(item) for item in data]
    elif isinstance(data, str):
        if len(data) > 4000:
            return translate_large_string(data)
        else:
            protected_text, dynamic_keys, html_tags = protect_special_content(data)
            translated_text = translator.translate(protected_text)
            return restore_special_content(translated_text, dynamic_keys, html_tags)
    else:
        return data

def process_and_translate_file(file_path, output_folder):
    with open(file_path, 'r', encoding='utf-8') as json_file:
        data = json.load(json_file)
    translated_data = translate_json_values(data)
    os.makedirs(output_folder, exist_ok=True)
    file_name = os.path.basename(file_path)
    translated_file_path = os.path.join(output_folder, file_name)

    with open(translated_file_path, 'w', encoding='utf-8') as json_file:
        json.dump(translated_data, json_file, ensure_ascii=False, indent=2)

    print(f"Translated file saved to: {translated_file_path}")

if __name__ == "__main__":
    input_folder_path = "./pt"  # Change this to your input folder
    output_folder_path = "./it"  # This is the folder for translated files

    for file_name in os.listdir(input_folder_path):
        if file_name.endswith('.json'):
            input_file_path = os.path.join(input_folder_path, file_name)
            output_file_path = os.path.join(output_folder_path, file_name)
            if os.path.exists(output_file_path):
                print(f"Skipping {file_name}, already translated.")
            else:
                process_and_translate_file(input_file_path, output_folder_path)
