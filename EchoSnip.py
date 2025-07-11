import os
import re
import yaml
import time
import glob
from datetime import datetime
import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
import sys

#**% Global variable
CONFIG = {}

#**% Color palette
COLOR_PRIMARY_BACKGROUND = "#1F2020"
COLOR_SECONDARY_BACKGROUND = "#1B1B1B"
COLOR_TEXT = "#fcfcfc"
COLOR_TEXT_EMPHASIS = "#000000"
COLOR_PLACEHOLDER = "#7A8088"
COLOR_ACCENT = "#d5f1ec"
COLOR_ACCENT_HOVER = "#a8c7c1"
COLOR_DISABLED_FG = "#888888"
COLOR_DISABLED_BG = "#333333"
FONT_FAMILY_UI = "Segoe UI"
FONT_FAMILY_CODE = "Consolas"

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
    try:
        with open(path, "r") as f:
            CONFIG = yaml.safe_load(f)
        debug_log(f"Config file loaded successfully from '{path}'.")
        return True
    except FileNotFoundError:
        messagebox.showerror("Fatal Error", f"Config file '{path}' not found.\nPlease ensure 'config.yaml' exists in the same directory as the application.")
        return False
    except Exception as e:
        messagebox.showerror("Fatal Error", f"Could not read or parse config file:\n{e}")
        return False

#**% Extract identation block
def extract_identation_block(lines, start_idx):
    debug_log("-> Running extract_identation_block")
    block_start_idx = -1
    for i in range(start_idx + 1, len(lines)):
        if lines[i].strip():
            block_start_idx = i
            break
    if block_start_idx == -1:
        debug_log("-> No non-empty lines found after marker. Returning empty block.", "WARN")
        return "", start_idx

    base_indent = len(lines[block_start_idx]) - len(lines[block_start_idx].lstrip())
    debug_log(f"-> Block starts on line {block_start_idx + 1}. Base indentation is {base_indent} spaces.")
    block_lines = []
    end_line_idx = len(lines) -1
    for i in range(block_start_idx, len(lines)):
        line = lines[i]
        if i > block_start_idx and line.strip():
            current_indent = len(line) - len(line.lstrip())
            if current_indent <= base_indent:
                end_line_idx = i - 1
                break
        block_lines.append(line)

    result = "".join(block_lines).rstrip()
    debug_log(f"-> Indentation block extracted. Length: {len(result)} chars, ends at line {end_line_idx + 1}.")
    return result, end_line_idx

#**% Extract brace block
def extract_brace_block(lines, start_idx):
    debug_log("-> Running extract_brace_block")
    block_start_idx = -1
    for i in range(start_idx + 1, len(lines)):
        if '{' in lines[i]:
            block_start_idx = i
            break
    if block_start_idx == -1:
        debug_log("-> No opening brace '{' found after marker. Returning empty block.", "WARN")
        return "", start_idx
    
    debug_log(f"-> Block starts on line {block_start_idx + 1} with first opening brace.")
    block_lines = []
    brace_count = 0
    end_line_idx = len(lines) -1
    for i in range(block_start_idx, len(lines)):
        line = lines[i]
        block_lines.append(line)
        brace_count += line.count('{')
        brace_count -= line.count('}')
        if brace_count <= 0:
            end_line_idx = i
            break
            
    result = "".join(block_lines).rstrip()
    debug_log(f"-> Brace block extracted. Length: {len(result)} chars, ends at line {end_line_idx + 1}.")
    return result, end_line_idx

#**% Extract marker block
def extract_marker_block(lines, start_idx, end_marker):
    debug_log(f"-> Running extract_marker_block, looking for end marker: '{end_marker}'")
    block = []
    end_line_idx = len(lines) -1
    for i in range(start_idx + 1, len(lines)):
        line = lines[i]
        if end_marker in line:
            end_line_idx = i
            break
        block.append(line)
    
    result = "".join(block).rstrip()
    debug_log(f"-> Marker block extracted. Length: {len(result)} chars, ends at line {end_line_idx + 1}.")
    return result, end_line_idx

SELF_CLOSING_TAGS = {'area', 'base', 'br', 'col', 'embed', 'hr', 'img', 'input', 'link', 'meta', 'param', 'source', 'track', 'wbr'}

#**% Extract HTML code block with tags
def extract_html_tag_block(lines, start_idx, identifier):
    debug_log("-> Running extract_html_tag_block")
    block_start_idx = -1
    first_tag_name = ""
    for i in range(start_idx + 1, len(lines)):
        line = lines[i].strip()
        if line.startswith('<') and not line.startswith('</') and identifier not in line:
            tag_name = line.split('>')[0].split(' ')[0].replace('<', '').lower()
            if tag_name not in SELF_CLOSING_TAGS:
                first_tag_name = tag_name
                block_start_idx = i
                break
    if block_start_idx == -1:
        debug_log("-> No non-self-closing HTML tag found after marker. Returning empty block.", "WARN")
        return "", start_idx
    
    debug_log(f"-> Block starts on line {block_start_idx + 1}. Tracking tag: '<{first_tag_name}>'")
    block_lines = []
    tag_balance = 0
    open_tag_regex = re.compile(r'<\s*' + re.escape(first_tag_name) + r'[\s>]', re.IGNORECASE)
    close_tag_regex = re.compile(r'</\s*' + re.escape(first_tag_name) + r'\s*>', re.IGNORECASE)
    end_line_idx = len(lines) - 1
    for i in range(block_start_idx, len(lines)):
        line = lines[i]
        block_lines.append(line)
        tag_balance += len(re.findall(open_tag_regex, line))
        tag_balance -= len(re.findall(close_tag_regex, line))
        if tag_balance <= 0:
            end_line_idx = i
            break
            
    result = "".join(block_lines).rstrip()
    debug_log(f"-> HTML tag block extracted. Length: {len(result)} chars, ends at line {end_line_idx + 1}.")
    return result, end_line_idx

#**% Find snippet based on keyword in files
def find_snippets_by_keyword(keywords, language):
    found_snippets_keys = set()
    lang_info = CONFIG['languages'][language]
    folder_path = CONFIG['folder_path']
    ignore_folders = set(CONFIG.get('ignore_folders', []))
    extensions_to_find = lang_info['extensions']

    debug_log(f"Starting generator search in folder: '{folder_path}' for language '{language}'.")

    for root, dirs, _ in os.walk(folder_path, topdown=True):
        dirs[:] = [d for d in dirs if d not in ignore_folders]
        
        relevant_files = []
        for ext in extensions_to_find:
            relevant_files.extend(glob.glob(os.path.join(root, f"*{ext}")))

        for file_path in relevant_files:
            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    lines = f.readlines()
                
                i = 0
                while i < len(lines):
                    line = lines[i]
                    is_marker_line = line.strip().startswith(lang_info['comment_start']) and lang_info['identifier'] in line
                    if is_marker_line and all(kw in line.lower() for kw in keywords):
                        clean_desc = line.strip().replace(lang_info['comment_start'], '', 1)
                        if 'comment_end' in lang_info: clean_desc = clean_desc.replace(lang_info['comment_end'], '', 1)
                        clean_desc = clean_desc.replace(lang_info['identifier'], '').strip()
                        
                        file_base_name = os.path.splitext(os.path.basename(file_path))[0]
                        unique_key = (file_base_name, clean_desc)

                        if unique_key not in found_snippets_keys:
                            found_snippets_keys.add(unique_key)
                            block_type = lang_info['block_type']
                            block_content = ""
                            if block_type == "indentation": block_content, _ = extract_identation_block(lines, i)
                            elif block_type == "brace": block_content, _ = extract_brace_block(lines, i)
                            elif block_type == 'html_tag': block_content, _ = extract_html_tag_block(lines, i, lang_info['identifier'])
                            elif block_type == "marker":
                                end_marker = lang_info.get('end_marker', f"{lang_info['identifier']} END")
                                block_content, _ = extract_marker_block(lines, i, end_marker)
                            
                            if block_content:
                                header = f"--- SNIPPET FOUND IN: {file_path} (Line {i+1}) ---\n"
                                header += f"--- DESCRIPTION: {clean_desc} ---\n\n"
                                
                                yield header + block_content
                    i += 1
            except Exception as e:
                debug_log(f"ERROR: Could not process {file_path}: {e}")

#**% Tkinter GUI
class EchoSnipApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("EchoSnip")
        self.geometry("1000x800")
        
        self._setup_styles()
        self.configure(bg=COLOR_PRIMARY_BACKGROUND)

        self.desc_placeholder = "Enter a description to search for..."
        self.lang_placeholder = "Language"

        main_frame = ttk.Frame(self, padding="10", style="App.TFrame")
        main_frame.pack(fill="both", expand=True)
        
        input_frame = ttk.Frame(main_frame, style="App.TFrame")
        input_frame.pack(fill="x", pady=(0, 5))
        
        self.desc_entry = ttk.Entry(input_frame, style="App.TEntry")
        self.desc_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.desc_entry.bind("<FocusIn>", self._clear_placeholder_desc)
        self.desc_entry.bind("<FocusOut>", self._add_placeholder_desc)
        self._add_placeholder_desc()

        lang_options = list(CONFIG.get('languages', {}).keys())
        
        self.lang_combobox = ttk.Combobox(input_frame, values=lang_options, state="readonly", width=15, style="App.TCombobox")
        self.lang_combobox.pack(side="left", padx=5)
        self.lang_combobox.set(self.lang_placeholder)
        self.lang_combobox.bind("<<ComboboxSelected>>", self._update_combobox_style)
        self._update_combobox_style()
        
        self.search_button = ttk.Button(input_frame, text="Search", command=self.perform_search, style="Round.TButton")
        self.search_button.pack(side="left", padx=5)
            
        results_frame = ttk.Frame(main_frame, style="App.TFrame")
        results_frame.pack(fill="both", expand=True, pady=(10, 0))
        
        self.results_text = tk.Text(results_frame, wrap="word", background=COLOR_SECONDARY_BACKGROUND,
                                    foreground=COLOR_TEXT, insertbackground=COLOR_TEXT, selectbackground=COLOR_ACCENT,
                                    selectforeground=COLOR_TEXT_EMPHASIS, relief="flat", borderwidth=0,
                                    font=(FONT_FAMILY_CODE, 10))
        
        scrollbar = ttk.Scrollbar(results_frame, orient="vertical", command=self.results_text.yview) 
        self.results_text.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side="right", fill="y")
        self.results_text.pack(side="left", fill="both", expand=True)

        self.search_generator = None
        self.snippet_count = 0
        self.start_time = 0

    def _add_placeholder_desc(self, event=None):
        if not self.desc_entry.get():
            self.desc_entry.insert(0, self.desc_placeholder)
            self.desc_entry.config(style="Placeholder.TEntry")

    def _clear_placeholder_desc(self, event=None):
        if self.desc_entry.get() == self.desc_placeholder:
            self.desc_entry.delete(0, "end")
            self.desc_entry.config(style="App.TEntry")

    def _update_combobox_style(self, event=None):
        if self.lang_combobox.get() == self.lang_placeholder:
            self.lang_combobox.config(style="Placeholder.TCombobox")
        else:
            self.lang_combobox.config(style="App.TCombobox")
                                     
    def _setup_styles(self):
        style = ttk.Style(self)
        style.theme_use('clam')

        style.configure('TFrame', background=COLOR_PRIMARY_BACKGROUND)
        style.configure('App.TFrame', background=COLOR_PRIMARY_BACKGROUND)
        
        style.configure('App.TEntry', fieldbackground=COLOR_SECONDARY_BACKGROUND, foreground=COLOR_TEXT,
                        insertcolor=COLOR_TEXT, borderwidth=0, relief='flat', font=(FONT_FAMILY_UI, 10))
        style.configure('Placeholder.TEntry', fieldbackground=COLOR_SECONDARY_BACKGROUND, foreground=COLOR_PLACEHOLDER,
                        insertcolor=COLOR_TEXT, borderwidth=0, relief='flat', font=(FONT_FAMILY_UI, 10))

        style.configure('App.TCombobox', fieldbackground=COLOR_SECONDARY_BACKGROUND, background=COLOR_SECONDARY_BACKGROUND,
                        arrowcolor=COLOR_TEXT, foreground=COLOR_TEXT, borderwidth=0, relief='flat',
                        font=(FONT_FAMILY_UI, 10))
        style.configure('Placeholder.TCombobox', fieldbackground=COLOR_SECONDARY_BACKGROUND, background=COLOR_SECONDARY_BACKGROUND,
                        arrowcolor=COLOR_TEXT, foreground=COLOR_PLACEHOLDER, borderwidth=0, relief='flat',
                        font=(FONT_FAMILY_UI, 10))
        self.option_add('*TCombobox*Listbox.background', COLOR_SECONDARY_BACKGROUND)
        self.option_add('*TCombobox*Listbox.foreground', COLOR_TEXT)
        self.option_add('*TCombobox*Listbox.selectBackground', COLOR_ACCENT)
        self.option_add('*TCombobox*Listbox.selectForeground', COLOR_TEXT_EMPHASIS)
        self.option_add('*TCombobox*Listbox.font', (FONT_FAMILY_UI, 10))
        self.option_add('*TCombobox*Listbox.relief', 'flat')
        self.option_add('*TCombobox*Listbox.borderwidth', 0)

        style.configure('TScrollbar',
                gripcount=0,
                background=COLOR_ACCENT,
                troughcolor=COLOR_PRIMARY_BACKGROUND,
                borderwidth=0,
                relief='flat',
                arrowcolor=COLOR_TEXT_EMPHASIS)
        style.map('TScrollbar', background=[('active', COLOR_ACCENT_HOVER)])

        style.layout('Round.TButton', [
            ('Button.button', {'children': [
                ('Button.focus', {'children': [
                    ('Button.padding', {'children': [
                        ('Button.label', {'sticky': 'nswe'})
                    ], 'sticky': 'nswe'})
                ], 'sticky': 'nswe'})
            ], 'sticky': 'nswe'})
        ])
        
        style.configure('Round.TButton',
            background=COLOR_ACCENT,
            foreground=COLOR_TEXT_EMPHASIS,
            font=(FONT_FAMILY_UI, 10, 'bold'),
            padding=(10, 5),
            borderwidth=0,
            relief='flat'
        )
        
        style.map('Round.TButton',
            background=[('active', COLOR_ACCENT_HOVER), ('disabled', COLOR_DISABLED_BG)],
            foreground=[('disabled', COLOR_DISABLED_FG)]
        )

    def perform_search(self):
        if self.search_generator:
            debug_log("Search cancelled because a new search was started.", "WARN")
        
        self.results_text.delete('1.0', tk.END)
        self.snippet_count = 0

        desc = self.desc_entry.get()
        lang = self.lang_combobox.get()
        
        if desc == self.desc_placeholder or not desc:
            self.results_text.insert('1.0', "Error: Please enter a description to search for.")
            return
        if lang == self.lang_placeholder or not lang:
            self.results_text.insert('1.0', "Error: Please select a language.")
            return

        self.search_button.config(state="disabled")
        self.results_text.insert('1.0', "Searching...")
        self.update_idletasks()
        
        keywords = desc.lower().split()
        debug_log(f"GUI search initiated. Language: '{lang}', Keywords: {keywords}")
        
        self.start_time = time.time()
        self.search_generator = find_snippets_by_keyword(keywords, lang)
        self.after(20, self._process_search_results)

    def _process_search_results(self):
        try:
            snippet = next(self.search_generator)
            
            if self.snippet_count == 0:
                self.results_text.delete('1.0', tk.END)
            
            self.snippet_count += 1
            
            self.results_text.delete('1.0', '2.0')
            header = f"---- Found {self.snippet_count} snippet(s) so far... ----\n"
            self.results_text.insert('1.0', header)
            
            self.results_text.insert(tk.END, snippet + "\n" + "=" * 70 + "\n")
            
            self.after(10, self._process_search_results)

        except StopIteration:
            
            elapsed_time = time.time() - self.start_time
            elapsed_str = f"Search completed in {elapsed_time:.2f} seconds"

            if self.snippet_count == 0:
                self.results_text.delete('1.0', tk.END)
                self.results_text.insert('1.0', f"---- Found 0 snippet(s) ----\n{elapsed_str}\n\nNo snippets found matching your criteria.")
            else:
                self.results_text.delete('1.0', '2.0')
                header = f"---- Found {self.snippet_count} snippet(s) ----\n---- {elapsed_str} ----\n"
                self.results_text.insert('1.0', header)
            
            self.search_generator = None
            self.search_button.config(state="normal")
            debug_log(f"GUI search process finished successfully in {elapsed_time:.2f}s.")
            
        except Exception as e:
            error_message = f"An error occurred during search: {e}"
            self.results_text.delete('1.0', tk.END)
            self.results_text.insert('1.0', error_message)

            self.search_generator = None
            self.search_button.config(state="normal")
            debug_log(f"GUI SEARCH ERROR: {e}", "ERROR")

#**% Main execution block
if __name__ == "__main__":
    if getattr(sys, 'frozen', False):
        application_path = os.path.dirname(sys.executable)
    else:
        application_path = os.path.dirname(os.path.abspath(__file__))

    config_path = os.path.join(application_path, 'config.yaml')

    if load_config(path=config_path):
        app = EchoSnipApp()
        app.mainloop()