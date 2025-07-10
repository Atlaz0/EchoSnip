import os
import re
import yaml
import time
from datetime import datetime
import tkinter as tk
from tkinter import ttk

#**% Global variable
CONFIG = {}

# --- [NEW] DEFINE YOUR COLOR PALETTE HERE ---
# Changed the accent color from blue to amber/orange as requested.
COLOR_PRIMARY_BACKGROUND = "#2b2b2b" # Dark grey
COLOR_SECONDARY_BACKGROUND = "#3c3f41" # Lighter grey for widgets
COLOR_TEXT = "#bbbbbb"                 # Light grey for normal text
COLOR_TEXT_EMPHASIS = "#ffffff"        # Pure white for important text
COLOR_PLACEHOLDER = "#8A8A8A"           # A dimmer grey for placeholder text
COLOR_ACCENT = "#ffc107"                # Amber/Orange for buttons and highlights
COLOR_ACCENT_HOVER = "#d39e00"          # A darker amber for when you hover
COLOR_DISABLED_FG = "#888888"          # Foreground (text) for disabled widgets
COLOR_DISABLED_BG = "#333333"          # Background for disabled widgets


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

# ... (All your file processing functions remain unchanged) ...
#**% Extract identation block
def extract_identation_block(lines, start_idx):
    debug_log(f" Running extract_identation_block, starting after line {start_idx + 1}")
    block_start_idx = -1
    for i in range(start_idx + 1, len(lines)):
        if lines[i].strip():
            block_start_idx = i
            break
    if block_start_idx == -1: return "", start_idx
    base_indent = len(lines[block_start_idx]) - len(lines[block_start_idx].lstrip())
    debug_log(f" Block starts on line {block_start_idx + 1}. Base indentation is {base_indent} spaces.")
    block_lines = []
    for i in range(block_start_idx, len(lines)):
        line = lines[i]
        if i > block_start_idx and line.strip():
            current_indent = len(line) - len(line.lstrip())
            if current_indent <= base_indent:
                return "".join(block_lines).rstrip(), i - 1
        block_lines.append(line)
    return "".join(block_lines).rstrip(), len(lines) - 1

#**% Extract brace block
def extract_brace_block(lines, start_idx):
    debug_log(f" Running extract_brace_block, starting after line {start_idx + 1}")
    block_start_idx = -1
    for i in range(start_idx + 1, len(lines)):
        if '{' in lines[i]:
            block_start_idx = i
            break
    if block_start_idx == -1: return "", start_idx
    block_lines = []
    brace_count = 0
    for i in range(block_start_idx, len(lines)):
        line = lines[i]
        block_lines.append(line)
        brace_count += line.count('{') - line.count('}')
        if brace_count <= 0:
            return "".join(block_lines).rstrip(), i
    return "".join(block_lines).rstrip(), i

#**% Extract marker block
def extract_marker_block(lines, start_idx, end_marker):
    debug_log(f" Running extract_marker_block from line {start_idx + 1}, looking for '{end_marker}'")
    block = []
    for i in range(start_idx + 1, len(lines)):
        line = lines[i]
        if end_marker in line:
            return "".join(block).rstrip(), i
        block.append(line)
    return "".join(block).rstrip(), i

SELF_CLOSING_TAGS = {'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 'link', 'meta', 'param', 'source', 'track', 'wbr'}

#**% Extract HTML code block with tags
def extract_html_tag_block(lines, start_idx, identifier):
    debug_log(f"Running extract_html_tag_block (stable specific-tag logic) starting after line {start_idx + 1}")
    block_start_idx = -1
    first_tag_name = ""
    for i in range(start_idx + 1, len(lines)):
        line = lines[i].strip()
        if line.startswith('<') and not line.startswith('</') and identifier not in line:
            tag_name = line.split('>')[0].split(' ')[0].replace('<', '').lower()
            if tag_name not in SELF_CLOSING_TAGS:
                first_tag_name = tag_name
                block_start_idx = i
                debug_log(f"Block starts on line {i + 1}. Tracking ONLY the tag: '<{first_tag_name}>'")
                break
    if block_start_idx == -1: return "", start_idx
    block_lines = []
    tag_balance = 0
    open_tag_regex = re.compile(r'<\s*' + re.escape(first_tag_name) + r'[\s>]', re.IGNORECASE)
    close_tag_regex = re.compile(r'</\s*' + re.escape(first_tag_name) + r'\s*>', re.IGNORECASE)
    for i in range(block_start_idx, len(lines)):
        line = lines[i]
        block_lines.append(line)
        tag_balance += len(re.findall(open_tag_regex, line))
        tag_balance -= len(re.findall(close_tag_regex, line))
        if tag_balance <= 0:
            return "".join(block_lines).rstrip(), i
    return "".join(block_lines).rstrip(), len(lines) - 1

#**% Find snippet based on keyword in files
def find_snippets_by_keyword(keywords, language):
    all_snippets = []
    found_snippets_keys = set()
    lang_info = CONFIG['languages'][language]
    extensions = lang_info['extensions']
    block_type = lang_info['block_type']
    identifier = lang_info['identifier'] 
    folder_path = CONFIG['folder_path']
    comment_start = lang_info.get('comment_start', '')
    comment_end = lang_info.get('comment_end', '')
    for root, _, files in os.walk(folder_path):
        for file in files:
            if not any(file.endswith(ext) for ext in extensions):
                continue
            file_path = os.path.abspath(os.path.join(root, file))
            debug_log(f" Scanning file: {file_path}")
            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    lines = f.readlines()
                i = 0
                while i < len(lines):
                    line = lines[i]
                    is_marker_line = line.strip().startswith(comment_start) and identifier in line
                    has_all_keywords = all(kw in line.lower() for kw in keywords)
                    if is_marker_line and has_all_keywords:
                        clean_desc = line.strip().replace(comment_start, '', 1)
                        if comment_end: clean_desc = clean_desc.replace(comment_end, '', 1)
                        clean_desc = clean_desc.replace(identifier, '').strip()
                        file_name_only = os.path.basename(file_path)
                        file_base_name, _ = os.path.splitext(file_name_only)
                        unique_key = (file_base_name, clean_desc)
                        if unique_key in found_snippets_keys:
                            debug_log(f" Duplicate snippet found for key ('{file_base_name}', '{clean_desc}'). Skipping.")
                        else:
                            found_snippets_keys.add(unique_key)
                            debug_log(f"MATCH FOUND on line {i+1}: '{line.strip()}' (Unique Key: {unique_key})")
                            block_content, end_line_index = "", i 
                            if block_type == "indentation": block_content, end_line_index = extract_identation_block(lines, i)
                            elif block_type == "brace": block_content, end_line_index = extract_brace_block(lines, i)
                            elif block_type == 'html_tag': block_content, end_line_index = extract_html_tag_block(lines, i, identifier)
                            elif block_type == "marker":
                                end_marker = lang_info.get('end_marker', f"{identifier} END")
                                block_content, end_line_index = extract_marker_block(lines, i, end_marker)
                            else:
                                debug_log(f"ERROR: Unknown block_type '{block_type}' for language '{language}'. Skipping.")
                                i += 1
                                continue
                            header = f"--- SNIPPET FOUND IN: {file_path} (Line {i+1}) ---\n"
                            header += f"--- DESCRIPTION: {clean_desc} ---\n\n"
                            all_snippets.append(header + block_content)
                    i += 1
            except Exception as e:
                debug_log(f"ERROR: Could not process {file_path}: {e}")
    return all_snippets


#**% Tkinter GUI
class EchoSnipApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("EchoSnip")
        self.geometry("1000x800")
        
        self._setup_styles()
        self.configure(bg=COLOR_PRIMARY_BACKGROUND)

        # --- [NEW] Define placeholder text strings ---
        self.desc_placeholder = "Enter a description to search for..."
        self.lang_placeholder = "Select a language..."

        main_frame = ttk.Frame(self, padding="10", style="App.TFrame")
        main_frame.pack(fill="both", expand=True)
        
        input_frame = ttk.Frame(main_frame)
        input_frame.pack(fill="x", pady=5)
        
        # --- [MODIFIED] Create Description Entry with Placeholder ---
        # The Label is removed. We will manage the placeholder text directly.
        self.desc_entry = ttk.Entry(input_frame)
        self.desc_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.desc_entry.bind("<FocusIn>", self._clear_placeholder_desc)
        self.desc_entry.bind("<FocusOut>", self._add_placeholder_desc)
        self._add_placeholder_desc() # Set the initial placeholder

        # --- [MODIFIED] Create Language Combobox with Placeholder ---
        # The Label is removed. The placeholder is now the first item in the list.
        lang_options = list(CONFIG.get('languages', {}).keys())
        lang_options.insert(0, self.lang_placeholder) # Add placeholder to the list
        
        self.lang_combobox = ttk.Combobox(input_frame, values=lang_options, state="readonly")
        self.lang_combobox.pack(side="left", padx=5)
        self.lang_combobox.set(self.lang_placeholder) # Set the initial value
        self.lang_combobox.bind("<<ComboboxSelected>>", self._update_combobox_style)
        self._update_combobox_style() # Set the initial text color
        
        # --- [MODIFIED] Use the new "Round.TButton" style ---
        self.search_button = ttk.Button(input_frame, text="Search", command=self.perform_search, style="Round.TButton")
        self.search_button.pack(side="left", padx=5)
            
        results_frame = ttk.Frame(main_frame)
        results_frame.pack(fill="both", expand=True, pady=10)
        
        self.results_text = tk.Text(results_frame, wrap="word", width=100, height=30, background=COLOR_SECONDARY_BACKGROUND,
                                    foreground=COLOR_TEXT, insertbackground=COLOR_TEXT_EMPHASIS, selectbackground=COLOR_ACCENT,
                                    selectforeground=COLOR_TEXT_EMPHASIS, relief="flat", borderwidth=1, highlightthickness=1,
                                    highlightbackground=COLOR_PRIMARY_BACKGROUND, highlightcolor=COLOR_ACCENT)
        
        scrollbar = ttk.Scrollbar(results_frame, orient="vertical", command=self.results_text.yview)
        self.results_text.configure(yscrollcommand=scrollbar.set)
        
        scrollbar.pack(side="right", fill="y")
        self.results_text.pack(side="left", fill="both", expand=True)
            
        self.status_bar = ttk.Label(main_frame, text="Ready.", anchor="w")
        self.status_bar.pack(side="bottom", fill="x")

    # --- [NEW] Methods for managing placeholder in Description Entry ---
    def _add_placeholder_desc(self, event=None):
        """Adds placeholder text if the entry is empty."""
        if not self.desc_entry.get():
            self.desc_entry.insert(0, self.desc_placeholder)
            self.desc_entry.config(foreground=COLOR_PLACEHOLDER)

    def _clear_placeholder_desc(self, event=None):
        """Clears placeholder text on focus."""
        if self.desc_entry.get() == self.desc_placeholder:
            self.desc_entry.delete(0, "end")
            self.desc_entry.config(foreground=COLOR_TEXT)

    # --- [NEW] Method for managing placeholder style in Language Combobox ---
    def _update_combobox_style(self, event=None):
        """Changes combobox text color based on whether it's a placeholder."""
        current_value = self.lang_combobox.get()
        if current_value == self.lang_placeholder:
            # When the placeholder is showing, use the placeholder color
            self.lang_combobox.config(foreground=COLOR_PLACEHOLDER)
        else:
            # When a real language is selected, use the normal text color
            self.lang_combobox.config(foreground=COLOR_TEXT)
                                     
    def _setup_styles(self):
        style = ttk.Style(self)
        style.theme_use('clam')

        # --- General Widget Configurations ---
        style.configure('TFrame', background=COLOR_PRIMARY_BACKGROUND)
        style.configure('App.TFrame', background=COLOR_PRIMARY_BACKGROUND)
        style.configure('TLabel', background=COLOR_PRIMARY_BACKGROUND, foreground=COLOR_TEXT, font=('Segoe UI', 10))
        
        style.configure('TEntry', fieldbackground=COLOR_SECONDARY_BACKGROUND, foreground=COLOR_TEXT,
                        insertcolor=COLOR_TEXT_EMPHASIS, borderwidth=0, relief='flat')
        
        # --- [MODIFIED] Combobox Style ---
        # We now use a direct .config() in the placeholder methods to handle the
        # foreground color dynamically, so we set the default here.
        style.configure('TCombobox', fieldbackground=COLOR_SECONDARY_BACKGROUND, background=COLOR_SECONDARY_BACKGROUND,
                        arrowcolor=COLOR_TEXT, foreground=COLOR_TEXT, borderwidth=0, relief='flat')
        self.option_add('*TCombobox*Listbox.background', COLOR_SECONDARY_BACKGROUND)
        self.option_add('*TCombobox*Listbox.foreground', COLOR_TEXT)
        self.option_add('*TCombobox*Listbox.selectBackground', COLOR_ACCENT)
        self.option_add('*TCombobox*Listbox.selectForeground', COLOR_TEXT_EMPHASIS)

        # --- [MODIFIED] Scrollbar Style (uses new ACCENT color) ---
        style.configure('TScrollbar', gripcount=0, background=COLOR_ACCENT, troughcolor=COLOR_SECONDARY_BACKGROUND,
                        borderwidth=0, relief='flat', arrowcolor=COLOR_SECONDARY_BACKGROUND)
        style.map('TScrollbar', background=[('active', COLOR_ACCENT_HOVER)])

        # --- [NEW] Round Button Style ---
        # This is an advanced technique. We are defining a custom layout for a button,
        # telling it to use a 'button' element (which respects the background color)
        # as its main component, effectively creating a custom shape.
        style.layout('Round.TButton', [
            ('Button.button', {'children': [
                ('Button.focus', {'children': [
                    ('Button.padding', {'children': [
                        ('Button.label', {'sticky': 'nswe'})
                    ], 'sticky': 'nswe'})
                ], 'sticky': 'nswe'})
            ], 'sticky': 'nswe'})
        ])
        
        # Now we configure our new 'Round.TButton' style
        style.configure('Round.TButton',
            background=COLOR_ACCENT,
            foreground=COLOR_TEXT_EMPHASIS,
            font=('Segoe UI', 10, 'bold'),
            padding=(10, 5),
            borderwidth=0,
            relief='flat'
        )
        
        style.map('Round.TButton',
            background=[('active', COLOR_ACCENT_HOVER), ('disabled', COLOR_DISABLED_BG)],
            foreground=[('disabled', COLOR_DISABLED_FG)]
        )

    def perform_search(self):
        desc = self.desc_entry.get()
        lang = self.lang_combobox.get()
        
        # --- [MODIFIED] Validation for placeholder text ---
        if desc == self.desc_placeholder or not desc:
            self.status_bar.config(text="Error: Please enter a description.")
            return
        if lang == self.lang_placeholder or not lang:
            self.status_bar.config(text="Error: Please select a language.")
            return

        self.status_bar.config(text="Searching...")
        self.results_text.delete('1.0', tk.END)
        self.search_button.config(state="disabled")
        self.update_idletasks()
        try:
            keywords = desc.lower().split()
            start_time = time.time()
            results = find_snippets_by_keyword(keywords, lang)
            elapsed_time = time.time() - start_time
            elapsed_str = f"Search completed in {elapsed_time:.2f} seconds"
            output_lines = [f"---- Found {len(results)} snippet(s) ----", elapsed_str + "\n"]
            if not results:
                output_lines.append("No snippets found matching your criteria.")
            else:
                for snippet in results:
                    output_lines.append(snippet)
                    output_lines.append("=" * 70)
            self.results_text.insert('1.0', "\n".join(output_lines))
            self.status_bar.config(text=elapsed_str)
        except Exception as e:
            error_message = f"An error occurred: {e}"
            self.results_text.insert('1.0', error_message)
            self.status_bar.config(text="Error.")
            debug_log(f"GUI SEARCH ERROR: {e}")
        finally:
            self.search_button.config(state="normal")

#**% Main execution block
if __name__ == "__main__":
    load_config()
    app = EchoSnipApp()
    app.mainloop()

"""
# This is the old, unused command-line logic for debugging or reference
def get_user_input():
    print("Enter description: ")
    desc = input()

    supported_langs = ", ".join(CONFIG['languages'].keys())
    print(f"Supported languages: {supported_langs}")
    print("Enter language name (e.g., Python, HTML):")
    lang_name = input()

    lang_name_lower = lang_name.lower()
    for key in CONFIG['languages'].keys():
        if key.lower() == lang_name_lower:
            debug_log(f" User input received. Description: '{desc}', Language: '{key}'.")
            return desc, key
    
    debug_log(f" User entered language '{lang_name}', which is NOT in the config.")
    debug_log(f" Error: '{lang_name}' is not a supported language in your config.")
    return None, None

def old_main():
    desc, lang = get_user_input()
    
    if desc and lang:
        keywords = desc.lower().split()
        start_time = time.time()
        results = find_snippets_by_keyword(keywords, lang)
        elapsed_time = time.time() - start_time
        elapsed_str = f" Search completed in {elapsed_time:.2f} seconds"
    
        output_path = CONFIG['output_path']
        try:
            with open(output_path, 'w', encoding="utf-8") as file:
                file.write(f" ---- Found {len(results)} snippet(s) ----\n")
                file.write(elapsed_str + "\n\n")
                for snippet in results:
                    file.write(snippet + "\n" + "="*70 + "\n")
            debug_log(f" Results successfully written to '{output_path}'")
            debug_log(elapsed_str)
        except Exception as e:
            debug_log(f" ERROR: Failed to write to output file '{output_path}': {e}")
        debug_log(" Script execution completed.")
        debug_log()
"""