import os
import yaml
from datetime import datetime

#**% Global variable
CONFIG = {}

#**% Write debug to debug file
def debug_log(message=None, level="DEBUG"):
    if not CONFIG.get('debug', False):
        return
    
    debug_path = CONFIG.get('debug_log_path', 'debug.log')
    
    with open(debug_path, "a", encoding="utf-8") as f:
        if message is None:
            f.write("\n\n")
            return
        
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        message = message.strip()
        lines = message.splitlines()
        formatted_lines = [f"{timestamp} {level}: {line}" for line in lines]

        for line in formatted_lines:
            f.write(line + "\n")

#**% Load config file
def load_config(path="config.yaml"):
    global CONFIG
    debug_log(f" Attempting to load config file from '{path}'...")
    try:
        with open(path, "r") as f:
            CONFIG = yaml.safe_load(f)
        debug_log(" Config file loaded successfully.")
    except FileNotFoundError:
        debug_log(f" FATAL ERROR: Config file '{path}' not found. Please ensure it exists.")
        exit(1)
    except Exception as e:
        debug_log(f" FATAL ERROR: Could not read or parse config file: {e}")
        exit(1)

#**% Get user input
def get_user_input():
    print("Enter description: ")
    desc = input()

    supported_langs = ", ".join(CONFIG['languages'].keys())
    print(f"\nSupported languages: {supported_langs}")
    print("Enter language name (e.g., python, html):")
    lang_name = input()
    
    if lang_name not in CONFIG['languages']:
        debug_log(f" User entered language '{lang_name}', which is NOT in the config.")
        debug_log(f" Error: '{lang_name}' is not a supported language in your config.")
        return None, None
    
    debug_log(f" User input received. Description: '{desc}', Language: '{lang_name}'.")
    return desc, lang_name

#**% Extract identation block
def extract_identation_block(lines, start_idx):
    debug_log(f" Running extract_identation_block from line {start_idx}")
    first_line_index = -1
    for i in range(start_idx, len(lines)):
            if lines[i].strip():
                first_line_index = i
            break
    if first_line_index == -1: 
        debug_log(" < No content found for indentation block.")
        return "", len(lines)

    base_indent = len(lines[first_line_index]) - len(lines[first_line_index].lstrip())
    debug_log(f" Base indentation is {base_indent} spaces.")
    block = []

    for i in range(first_line_index, len(lines)):
        line = lines[i]
        if line.strip() and (len(line) - len(line.lstrip()) < base_indent):
            debug_log(f" Indentation block ended at line {i}.")
            return "".join(block), i - 1
        block.append(line)
    
    debug_log(" Indentation block reached end of file.")
    return "".join(block), len(lines) - 1

#**% Extract brace block
def extract_brace_block(lines, start_idx):
    debug_log(f" Running extract_brace_block from line {start_idx}")
    block = []
    brace_count = 0
    started = False
    for i in range(start_idx, len(lines)):
        line = lines[i]
        if not started and '{' in line:
            started = True
        
        if started:
            block.append(line)
            brace_count += line.count('{') - line.count('}')
            if brace_count <= 0:
                debug_log(f" Brace block ended at line {i}.")
                return "".join(block), i
    debug_log(f" Brace block reached end of file.")
    return "".join(block), i

#**% Extract marker block
def extract_marker_block(lines, start_idx, end_marker):
    debug_log(f" Running extract_marker_block from line {start_idx}, looking for '{end_marker}'")
    block = []
    for i in range(start_idx, len(lines)):
        line = lines[i]
        if end_marker in line:
            debug_log(f" Marker block ended at line {i}.")
            return "".join(block), i
        block.append(line)
    debug_log(f" Marker block reached end of file.")
    return "".join(block), i

#**% Find snippet based on identifier in files
def find_snippets_by_keyword(keywords, language):
    all_snippets = []
    
    #Get settings from config
    lang_info = CONFIG['languages'][language]
    extensions = lang_info['extensions']
    block_type = lang_info['block_type']
    folder_path = CONFIG['folder_path']
    identifier = CONFIG['identifier']
    end_marker = f"{identifier} END"
    debug_log(f" --- Starting Search ---")
    debug_log(f" Searching for keywords: {keywords}")
    debug_log(f" In language: '{language}' with extensions {extensions}")
    debug_log(f" In folder: '{folder_path}'")
    debug_log(f" Using identifier: '{identifier}'")
    debug_log(f" Using block type: '{block_type}'")
    debug_log(f" -"*40)

    #Walk through files
    for root, _, files in os.walk(folder_path):
        for file in files:
            if not any(file.endswith(ext) for ext in extensions):
                continue
    
            file_path = os.path.join(root, file)
            debug_log(f" Scanning file: {file_path}")

            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    lines = f.readlines()
                
                i = 0
                while i < len(lines):
                    line = lines[i]
                    
                    #Check for a match in a line
                    has_identifier = identifier in line
                    has_all_keywords = all(kw in line.lower() for kw in keywords)

                    if has_identifier and has_all_keywords:
                        debug_log(f" MATCH FOUND on line {i+1}: '{line.strip()}'")
                        
                        start_of_block_index = i + 1
                        
                        #Call the correct block extractor
                        if block_type == "indentation":
                            code, end_index = extract_identation_block(lines, start_of_block_index)
                        elif block_type == "braces":
                            code, end_index = extract_brace_block(lines, start_of_block_index)
                        elif block_type == "marker":
                            code, end_index = extract_marker_block(lines, start_of_block_index, end_marker)
                        else:
                            debug_log(f" Unknown block type '{block_type}', skipping.")
                            i += 1
                            continue 
                        
                        debug_log(f" Extracted a block of code ending at line {end_index+1}. Adding to results.")
                        header = f" --- SNIPPET FOUND IN: {file_path} (Line {i+1}) ---\n"
                        header += f" --- DESCRIPTION: {line.strip()} ---\n\n"
                        all_snippets.append(header + code)
            
                        #CRUCIAL - Skip the loop counter
                        debug_log(f" Skipping main loop to line {end_index + 2}.")
                        i = end_index + 1
                        continue
            
                    i += 1
            except Exception as e:
                debug_log(f" ERROR: Could not process {file_path}: {e}")
                
    return all_snippets

#**% Main execution block
if __name__ == "__main__":
    load_config()
    desc, lang = get_user_input()
    
    if desc and lang:
        keywords = desc.lower().split()
        
        results = find_snippets_by_keyword(keywords, lang)
    
        output_path = CONFIG['output_path']
        try:
            with open(output_path, 'w') as file:
                file.write(f"\n--- Found {len(results)} snippet(s) ---\n\n")
                for snippet in results:
                    file.write(snippet + "\n" + "="*70 + "\n")
            debug_log(f" Results successfully written to '{output_path}'")
        except Exception as e:
            debug_log(print(f" ERROR: Failed to write to output file '{output_path}': {e}"))
        print("="*75)

        debug_log(" Script execution completed.")
        debug_log()