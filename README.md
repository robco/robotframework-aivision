[!["Buy Me A Coffee"](https://www.buymeacoffee.com/assets/img/custom_images/orange_img.png)](https://www.buymeacoffee.com/robco)
# Robot Framework GenAI Testing Library

GenAI testing library for Robot Framework that verifies UI/screenshots (including template “look & feel”) by sending instructions plus one or more images to an OpenAI-compatible API (Ollama, OpenAI, Perplexity, Gemini, etc.).

The main keyword (`Verify That`) expects the model to return a strict `RESULT:` / `EXPLANATION:` format and will fail the test if the result is not `pass`.

## Features

- Visual assertions on one or more screenshots using natural-language instructions.
- Template comparison keyword to validate “actual vs expected” look & feel (optionally creates a side-by-side image).
- Image utilities built on Pillow: open/convert, watermark, combine images, auto-generate names, save into Robot Framework output directory.
- Works with multiple providers via the `openai` Python client and OpenAI-compatible endpoints (`base_url`).

## Installation

**Install from PyPI (once published):**
```bash
pip install -U robotframework-ailibrary
```

Runtime dependencies include Robot Framework, Pillow, and the `openai` Python client.

## Configuration

Import the library in Robot Framework and choose a provider using `platform` plus optional overrides (`base_url`, `api_key`, `model`, `image_detail`).

### Robot Framework import examples

**Default (Ollama-like local setup):**
```robotframework
*** Settings ***
Library  AILibrary
```

**OpenAI (API key required):**
```robotframework
*** Settings ***
Library  AILibrary
... platform=OpenAI
... api_key=%{OPENAI_API_KEY}
... model=gpt-5.2
```

**Perplexity:**
```robotframework
*** Settings ***
Library  AILibrary
... platform=Perplexity
... api_key=%{PPLX_API_KEY}
... model=sonar-pro
```

**Gemini (OpenAI-compatible endpoint):**
```robotframework
*** Settings ***
Library  AILibrary
... platform=Gemini
... api_key=%{GEMINI_API_KEY}
... model=gemini-2.5-flash
```

### Supported platforms (defaults)

The library defines these platform presets (model and `base_url`) which you can override via import arguments.

| Platform | Default `base_url` | Default model | API key |
|---|---|---|---|
| Ollama | `http://localhost:11434/v1` | `qwen3-coder:480b-cloud` | Not required |
| DockerModel | `http://localhost:12434/engines/v1` | `ai/qwen3-vl:8B-Q8_K_XL` | Not required. |
| OpenAI | `https://api.openai.com/v1` | `gpt-5.2` | Required. |
| Perplexity | `https://api.perplexity.ai` | `sonar-pro` | Required. |
| Gemini | `https://generativelanguage.googleapis.com/v1beta/openai/` | `gemini-2.5-flash` | Required. |
| Manual | `None` | `None` | Required. |

## Keywords

All keywords below are implemented in `AILibrary` and are available after importing the library.

| Keyword | Purpose |
|---|---|
| `Verify That` | Send one or more screenshots + instructions to the model, parse the `RESULT` and raise `AssertionError` on failure. |
| `Verify Screenshot Matches Look And Feel Template` | Compare a screenshot against a reference template with a built-in instruction set; optional combined image creation. |
| `Open Image` | Open an image (and optionally convert mode, default `RGB`). |
| `Save Image` | Save a PIL image to a path (defaults to RF output directory) with optional watermark. |
| `Generate Image Name` | Create a unique timestamp-based filename with prefix/extension. |
| `Combine Images On Paths Side By Side` | Combine two image files side-by-side (optionally watermark) and optionally save. |
| `Combine Images Side By Side` | Combine two in-memory PIL images side-by-side (optionally watermark). |
| `Add Watermark To Image` | Add watermark text using the included font file. |

## Usage examples

### Simple visual assertion

```robotframework
*** Settings ***
Library  AILibrary  platform=Ollama

*** Test Cases ***
Login button is correct
   Verify That  ${CURDIR}/screens/login.png  Login button is visible and labeled as 'Sign In'
```

### Compare screenshot to design template

```robotframework
*** Settings ***
Library  AILibrary

*** Test Cases ***
Home page matches template
   Verify Screenshot Matches Look And Feel Template
   ...  ${CURDIR}/screens/home_actual.png
   ...  ${CURDIR}/templates/home_expected.png
```

### Override template instructions

```robotframework
*** Settings ***
Library  AILibrary

*** Test Cases ***
Home page matches template - custom rules
   Verify Screenshot Matches Look And Feel Template
   ...  ${CURDIR}/screens/home_actual.png
   ...  ${CURDIR}/templates/home_expected.png
   ...  override_instructions=Verify layout, spacing, typography, and brand colors match the template exactly.
```
