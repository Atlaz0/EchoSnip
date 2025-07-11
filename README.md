      
# EchoSnip

![MIT License](https://img.shields.io/badge/License-MIT-blue.svg)

**EchoSnip is a blazingly fast, local-first code snippet manager that finds and extracts complete code blocks directly from your files.**

Stop hunting through old projects for that perfect function or component. With EchoSnip, you can tag your best code with a simple comment and recall it instantly with a keyword search.

![App preview](https://res.cloudinary.com/deftgalbo/image/upload/v1752245655/Screenshot_2025-07-11_175350_yismfq.png)

## Key Features

-   **Extremely Fast:** Searches your local codebase in milliseconds.
-   **Language Agnostic:** Works with any programming language thanks to its configurable parsing engine. Comes pre-configured for over 15 popular languages.
-   **Intelligent Block Extraction:** Understands code blocks based on indentation (Python), braces `{}` (C++, JS), HTML tags, or custom start/end markers.
-   **Simple & Clean:** A functional, dark-themed GUI that is intuitive and easy to use.
-   **Fully Configurable:** All settings, languages, and paths are controlled through a single `config.yaml` file.

## How It Works

EchoSnip isn't just a text search tool. It works in two steps:

1.  It finds the special **marker comment** you've written (e.g., `#**% A reusable database connection`).
2.  Based on the rules you've set for that language, it intelligently **extracts the entire code block** that follows the comment, whether it's a function, a class, an HTML `<div>`, or a CSS rule.

This allows you to pull up complete, ready-to-use snippets, not just single lines of code.

## Installation

### For End-Users (Recommended)

1.  Go to the [Releases page](https://github.com/Atlaz0/EchoSnip/releases) on GitHub.
2.  Download the latest `EchoSnip.exe` file.

> **Important Note for Windows Users:**
>
> When you first run `EchoSnip.exe`, Windows Defender SmartScreen will likely show a blue pop-up screen that says "Windows protected your PC".
>
> **This is normal for new applications from individual developers.** Because the application is not "code signed" (an expensive process for hobbyists), Windows treats it with caution until it builds a reputation. The application is safe to use.
>
> To run the application, please follow these steps:
> 1. On the blue screen, click the `More info` link.
> 2. A new button will appear. Click `Run anyway`.
3.  Place the `.exe` file in a folder along with the `config.yaml` file.
4.  Run `EchoSnip.exe`. That's it!

### For Developers (Running from Source)

1.  Clone this repository:
    ```bash
    git clone https://github.com/Atlaz0/EchoSnip.git
    cd EchoSnip
    ```
2.  Create and activate a virtual environment:
    ```bash
    # On Windows
    python -m venv venv
    .\venv\Scripts\activate

    # On macOS/Linux
    python3 -m venv venv
    source venv/bin/activate
    ```
3.  Install the required dependencies:
    ```bash
    pip install -r requirements.txt
    ```

## How to Use

### 1. Configure Your `config.yaml`
Before the first run, you **must** configure the `config.yaml` file.

-   **Set Your Code Directory:** Open `config.yaml` and change the `folder_path` to the root directory where all your programming projects are stored.
    ```yaml
    # The top-level folder where your code projects are stored.
    folder_path: "C:/folder/path/to/projects"
    ```
-   **Review Languages:** EchoSnip comes with many languages pre-configured. You can add your own or modify existing ones. See the **Advanced Configuration** section below.

### 2. Tag Your Code
Go into any of your code files and add a special comment above a code block you want to save. The comment must use the format defined in your `config.yaml` (`comment_start` + `identifier`).

**Python Example (`#**%`):**
```python
#**% A function to parse user data
def parse_user(user_data):
    # ... implementation ...
    return user  

```
```html  
<!--**% Main hero section for the homepage -->
<section class="hero" id="hero">
    <h2>Welcome to My Site</h2>
    <p>This is a tagline.</p>
</section>
```

### 3. Run the Application

-   **If using the .exe:** Double-click `EchoSnip.exe`.
-   **If running from source:**
    ```bash
    python EchoSnip.py
    ```

Now you can search for "user data" or "hero section" in the app, select the language, and see your snippet appear instantly!

## Advanced Configuration (`config.yaml`)

You can teach EchoSnip to understand any language by adding an entry to the `languages` section of `config.yaml`.

```yaml
       
#### Field Descriptions:

-   `extensions`: A list of file extensions for the language.
-   `identifier`: The unique string in your comment marker that EchoSnip looks for.
-   `comment_start`: The character(s) that start a comment.
-   `comment_end`: (Optional) The character(s) that end a multi-line comment.
-   `block_type`: The core of the parsing engine.
    -   `indentation`: For languages like Python or YAML.
    -   `brace`: For languages that use `{}` (C++, Java, JS, CSS).
    -   `html_tag`: For HTML/XML, finds the corresponding closing tag.
    -   `marker`: A simple mode that captures everything until an `end_marker` is found (great for SQL or Shell).
-   `end_marker`: (Required for `marker` block_type) Defines the full comment that ends the snippet (e.g., `;**% END`).

## Contributing

Contributions are welcome! Whether it's reporting a bug, suggesting a feature, or submitting code—your help is appreciated. Please read our [**Contributing Guidelines**](CONTRIBUTING.md) to get started.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

    