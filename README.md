# vim-ai

This plugin adds Artificial Intelligence (AI) capabilities to your Vim and Neovim.
You can generate code, edit text, or have an interactive conversation with GPT models, all powered by OpenAI's API.

![vim-ai demo](./demo.gif)

To get an idea what is possible to do with AI commands see the [prompts](https://github.com/madox2/vim-ai/wiki/AI-prompts#prompts) on the [Community Wiki](https://github.com/madox2/vim-ai/wiki)

## Features

- Generate text or code, answer questions with AI
- Edit selected text in-place with AI
- Interactive conversation with ChatGPT
- Custom roles
- Vision capabilities (image to text)
- Generate images
- Integrates with any OpenAI-compatible API
- AI provider plugins

## How it works

This plugin uses OpenAI's API to generate responses.
You will need to [setup](https://platform.openai.com/signup) an account and obtain an [API key](https://platform.openai.com/account/api-keys).
Usage of the API is not free, but the cost is reasonable and depends on how many tokens you use, in simple terms, how much text you send and receive (see [pricing](https://openai.com/pricing)).
Note that the plugin does not send any of your code behind the scenes.
You only share and pay for what you specifically select, for prompts and chat content.

In case you would like to experiment with Gemini, Claude or other models running as a service or locally, you can use any OpenAI compatible proxy.
A simple way is to use [OpenRouter](https://openrouter.ai) which has a fair pricing (and currently offers many models for [free](https://openrouter.ai/models?max_price=0)), or setup a proxy like [LiteLLM](https://github.com/BerriAI/litellm) locally.
See this simple [guide](#example-create-custom-roles-to-interact-with-openrouter-models) on configuring custom OpenRouter roles.

🚨 **Announcement** 🚨

`vim-ai` can now be extended with custom provider plugins.
However, there aren't many available yet, so developing new ones is welcome!
For more, see the [providers](#providers) section.

## Table of Contents

- [Installation](#installation)
- [Usage](#usage)
- [Providers](#providers)
- [Roles](#roles)
- [Reference](#reference)
- [Configuration](#configuration)
- [Key bindings](#key-bindings)
- [Custom commands](#custom-commands)

## Installation

### Prerequisites

- Vim or Neovim compiled with python3 support
- [API key](https://platform.openai.com/account/api-keys)

```sh
# save api key to `~/.config/openai.token` file
echo "YOUR_OPENAI_API_KEY" > ~/.config/openai.token

# alternatively set it as an environment variable
export OPENAI_API_KEY="YOUR_OPENAI_API_KEY"

# or configure it with your organization id
echo "YOUR_OPENAI_API_KEY,YOUR_OPENAI_ORG_ID" > ~/.config/openai.token
export OPENAI_API_KEY="YOUR_OPENAI_API_KEY,YOUR_OPENAI_ORG_ID"
```

The default api key file location is `~/.config/openai.token`, but you can change it by setting the `g:vim_ai_token_file_path` in your `.vimrc` file:

```vim
let g:vim_ai_token_file_path = '~/.config/openai.token'
```

### Using `vim-plug`

```vim
Plug 'madox2/vim-ai'
```

### Manual installation

Using built-in Vim packages `:help packages`

```sh
# vim
mkdir -p ~/.vim/pack/plugins/start
git clone https://github.com/madox2/vim-ai.git ~/.vim/pack/plugins/start/vim-ai

# neovim
mkdir -p ~/.local/share/nvim/site/pack/plugins/start
git clone https://github.com/madox2/vim-ai.git ~/.local/share/nvim/site/pack/plugins/start/vim-ai
```

## Usage

To use an AI command, type the command followed by an instruction prompt. You can also combine it with a visual selection. Here is a brief overview of available commands:

```
========== Basic AI commands ==========

:AI          complete text
:AIEdit      edit text
:AIChat      continue or open new chat
:AIStopChat  stop the generation of the AI response for the AIChat
:AIImage     generate image

============== Utilities ==============

:AIRedo          repeat last AI command
:AIUtilRolesOpen open role config file
:AIUtilDebugOn   turn on debug logging
:AIUtilDebugOff  turn off debug logging

:help vim-ai
```

**Tip:** Press `Ctrl-c` anytime to cancel `:AI` and `:AIEdit` completion

**Tip:** Use command shortcuts - `:AIE`, `:AIC`, `:AIS`,`:AIR`, `:AII` or setup your own [key bindings](#key-bindings)

**Tip:** Define and use [custom roles](#roles), e.g. `:AIEdit /grammar`.

**Tip:** Use pre-defined roles `/right`, `/below`, `/tab` to choose how chat is open, e.g. `:AIC /right`

**Tip:** Use special role `/populate` to dump options to chat header, e.g. `:AIC /populate /gemini`

**Tip:** Combine commands with a range `:help range`, e.g. to select the whole buffer - `:%AIE fix grammar`

If you are interested in more tips or would like to level up your Vim with more commands like [`:GitCommitMessage`](https://github.com/madox2/vim-ai/wiki/Custom-commands#suggest-a-git-commit-message) - suggesting a git commit message, visit the [Community Wiki](https://github.com/madox2/vim-ai/wiki).

## Providers

This is the list of 3rd party provider plugins allowing to use different AI providers.

- [google provider](https://github.com/madox2/vim-ai-provider-google) - Google's Gemini models
- [OpenAI Responses API Provider](https://github.com/kevincojean/vim-ai-provider-openai-responses) - OpenAI Responses API compatibility plug-in
- [OpenAI Provider with MCP support](https://github.com/kracejic/vim-ai-provider-openai-mcp) - OpenAI chat with MCP

In case you are interested in developing one, have a look at reference [google provider](https://github.com/madox2/vim-ai-provider-google).
Do not forget to open PR updating this list.

## Roles

In the context of this plugin, a role means a re-usable AI instruction and/or configuration. Roles are defined in the configuration `.ini` file. For example by defining a `grammar` and `o1-mini` role:

```vim
let g:vim_ai_roles_config_file = '/path/to/my/roles.ini'
```

```ini
# /path/to/my/roles.ini

[grammar]
prompt = fix spelling and grammar
options.temperature = 0.4

[o1-mini]
options.stream = 0
options.model = o1-mini
options.max_completion_tokens = 25000
options.temperature = 1
options.initial_prompt =
```

Now you can select text and run it with command `:AIEdit /grammar`.

You can also combine roles `:AI /o1-mini /grammar helo world!`

See [roles-example.ini](./roles-example.ini) for more examples.

## Reference

In the documentation below,  `<selection>` denotes a visual selection or any other range, `{instruction}` an instruction prompt, `{role}` a [custom role](#roles) and `?` symbol an optional parameter.

### `:AI`

`:AI {prompt}` - complete the prompt

`<selection> :AI` - complete the selection

`<selection> :AI {instruction}` - complete the selection using the instruction

`<selection>? :AI /{role} {instruction}?` - use role to complete

### `:AIEdit`

`<selection>? :AIEdit` - edit the current line or the selection

`<selection>? :AIEdit {instruction}` - edit the current line or the selection using the instruction

`<selection>? :AIEdit /{role} {instruction}?` - use role to edit

### `:AIImage`

`:AIImage {prompt}` - generate image with prompt

`<selection> :AIImage` - generate image with seleciton

`<selection>? :AI /{role} {instruction}?` - use role to generate

[Pre-defined](./roles-default.ini) image roles: `/hd`, `/natural`

### `:AIChat`

`:AIChat` - continue or start a new conversation.

`<selection>? :AIChat {instruction}?` - start a new conversation given the selection, the instruction or both

`<selection>? :AIChat /{role} {instruction}?` - use role to complete

When the AI finishes answering, you can continue the conversation by entering insert mode, adding your prompt, and then using the command `:AIChat` once again.

[Pre-defined](./roles-default.ini) chat roles: `/right`, `/below`, `/tab`

#### `.aichat` files

You can edit and save the chat conversation to an `.aichat` file and restore it later.
This allows you to create re-usable custom prompts, for example:

```
# ./refactoring-prompt.aichat

>>> system

You are a Clean Code expert, I have the following code, please refactor it in a more clean and concise way so that my colleagues can maintain the code more easily. Also, explain why you want to refactor the code so that I can add the explanation to the Pull Request.

>>> user

[attach code]

```

To include files in the chat a special `include` section is used:

```
>>> user

Generate documentation for the following files

>>> include

/home/user/myproject/requirements.txt
/home/user/myproject/**/*.py
```

Each file's contents will be added to an additional user message with `==> {path} <==` header, relative paths are resolved to the current working directory.


To use image vision capabilities (image to text) include an image file:

```
>>> user

What object is on the image?

>>> include

~/myimage.jpg
```

Execute command and include stdout into the chat:

```
>>> user

Suggest git commit message

>>> exec

git diff
```

Supported chat sections are **`>>> system`**, **`>>> user`**, **`>>> include`**, **`>>> exec`** and **`<<< assistant`**

### `:AIRedo`

`:AIRedo` - repeat last AI command

Use this immediately after `AI`/`AIEdit`/`AIChat` command in order to re-try or get an alternative completion.
Note that the randomness of responses heavily depends on the [`temperature`](https://platform.openai.com/docs/api-reference/completions/create#completions/create-temperature) parameter.

## Configuration

Each command is configured with a corresponding configuration variable.
To customize the default configuration, initialize the config variable with a selection of options, for example put this to your`.vimrc` file:

```vim
let g:vim_ai_chat = {
\  "options": {
\    "model": "o1-preview",
\    "stream": 0,
\    "temperature": 1,
\    "max_completion_tokens": 25000,
\    "initial_prompt": "",
\  },
\}
```

Alternatively you can use special `default` role:

```ini
[default.chat]
options.model = o1-preview
options.stream = 0
options.temperature = 1
options.max_completion_tokens = 25000
options.initial_prompt =
```

Or customize the options directly in the chat buffer:

```properties
[chat]
options.model = o1-preview
options.stream = 0
options.temperature = 1
options.max_completion_tokens = 25000
options.initial_prompt =

>>> user

generate a paragraph of lorem ipsum
```

Below are listed all available configuration options, along with their default values.
Please note that there isn't any token limit imposed on chat model.

```vim
" This prompt instructs model to be consise in order to be used inline in editor
let s:initial_complete_prompt =<< trim END
>>> system

You are a general assistant.
Answer shortly, consisely and only what you are asked.
Do not provide any explanantion or comments if not requested.
If you answer in a code, do not wrap it in markdown code block.
END

" :AI
" - provider: AI provider
" - prompt: optional prepended prompt
" - options: openai config (see https://platform.openai.com/docs/api-reference/chat)
" - options.initial_prompt: prompt prepended to every chat request (list of lines or string)
" - options.request_timeout: request timeout in seconds
" - options.auth_type: API authentication method (bearer, api-key, none)
" - options.token_file_path: override global token configuration
" - options.token_load_fn: expression/vim function to load token
" - options.selection_boundary: selection prompt wrapper (eliminates empty responses, see #20)
" - ui.paste_mode: use paste mode (see more info in the Notes below)
let g:vim_ai_complete = {
\  "provider": "openai",
\  "prompt": "",
\  "options": {
\    "model": "gpt-4o",
\    "endpoint_url": "https://api.openai.com/v1/chat/completions",
\    "max_tokens": 0,
\    "max_completion_tokens": 0,
\    "temperature": 0.1,
\    "request_timeout": 20,
\    "stream": 1,
\    "auth_type": "bearer",
\    "token_file_path": "",
\    "token_load_fn": "",
\    "selection_boundary": "#####",
\    "initial_prompt": s:initial_complete_prompt,
\    "frequency_penalty": "",
\    "logit_bias": "",
\    "logprobs": "",
\    "presence_penalty": "",
\    "reasoning_effort": "",
\    "seed": "",
\    "stop": "",
\    "top_logprobs": "",
\    "top_p": "",
\  },
\  "ui": {
\    "paste_mode": 1,
\  },
\}

" :AIEdit
" - provider: AI provider
" - prompt: optional prepended prompt
" - options: openai config (see https://platform.openai.com/docs/api-reference/chat)
" - options.initial_prompt: prompt prepended to every chat request (list of lines or string)
" - options.request_timeout: request timeout in seconds
" - options.auth_type: API authentication method (bearer, api-key, none)
" - options.token_file_path: override global token configuration
" - options.token_load_fn: expression/vim function to load token
" - options.selection_boundary: selection prompt wrapper (eliminates empty responses, see #20)
" - ui.paste_mode: use paste mode (see more info in the Notes below)
let g:vim_ai_edit = {
\  "provider": "openai",
\  "prompt": "",
\  "options": {
\    "model": "gpt-4o",
\    "endpoint_url": "https://api.openai.com/v1/chat/completions",
\    "max_tokens": 0,
\    "max_completion_tokens": 0,
\    "temperature": 0.1,
\    "request_timeout": 20,
\    "stream": 1,
\    "auth_type": "bearer",
\    "token_file_path": "",
\    "token_load_fn": "",
\    "selection_boundary": "#####",
\    "initial_prompt": s:initial_complete_prompt,
\    "frequency_penalty": "",
\    "logit_bias": "",
\    "logprobs": "",
\    "presence_penalty": "",
\    "reasoning_effort": "",
\    "seed": "",
\    "stop": "",
\    "top_logprobs": "",
\    "top_p": "",
\  },
\  "ui": {
\    "paste_mode": 1,
\  },
\}

" This prompt instructs model to work with syntax highlighting
let s:initial_chat_prompt =<< trim END
>>> system

You are a general assistant.
If you attach a code block add syntax type after ``` to enable syntax highlighting.
END

" :AIChat
" - provider: AI provider
" - prompt: optional prepended prompt
" - options: openai config (see https://platform.openai.com/docs/api-reference/chat)
" - options.initial_prompt: prompt prepended to every chat request (list of lines or string)
" - options.request_timeout: request timeout in seconds
" - options.auth_type: API authentication method (bearer, api-key, none)
" - options.token_file_path: override global token configuration
" - options.token_load_fn: expression/vim function to load token
" - options.selection_boundary: selection prompt wrapper (eliminates empty responses, see #20)
" - ui.open_chat_command: preset (preset_below, preset_tab, preset_right) or a custom command
" - ui.populate_options: dump [chat] config to the chat header
" - ui.scratch_buffer_keep_open: re-use scratch buffer within the vim session
" - ui.force_new_chat: force new chat window (used in chat opening roles e.g. `/tab`)
" - ui.paste_mode: use paste mode (see more info in the Notes below)
let g:vim_ai_chat = {
\  "provider": "openai",
\  "prompt": "",
\  "options": {
\    "model": "gpt-4o",
\    "endpoint_url": "https://api.openai.com/v1/chat/completions",
\    "max_tokens": 0,
\    "max_completion_tokens": 0,
\    "temperature": 1,
\    "request_timeout": 20,
\    "stream": 1,
\    "auth_type": "bearer",
\    "token_file_path": "",
\    "token_load_fn": "",
\    "selection_boundary": "",
\    "initial_prompt": s:initial_chat_prompt,
\    "frequency_penalty": "",
\    "logit_bias": "",
\    "logprobs": "",
\    "presence_penalty": "",
\    "reasoning_effort": "",
\    "seed": "",
\    "stop": "",
\    "top_logprobs": "",
\    "top_p": "",
\  },
\  "ui": {
\    "open_chat_command": "preset_below",
\    "scratch_buffer_keep_open": 0,
\    "populate_options": 0,
\    "force_new_chat": 0,
\    "paste_mode": 1,
\  },
\}

" :AIImage
" - prompt: optional prepended prompt
" - options: openai config (https://platform.openai.com/docs/api-reference/images/create)
" - options.request_timeout: request timeout in seconds
" - options.auth_type: API authentication method (bearer, api-key, none)
" - options.token_file_path: override global token configuration
" - options.token_load_fn: expression/vim function to load token
" - options.download_dir: path to image download directory, `cwd` if not defined
let g:vim_ai_image = {
\  "provider": "openai",
\  "prompt": "",
\  "options": {
\    "model": "dall-e-3",
\    "endpoint_url": "https://api.openai.com/v1/images/generations",
\    "quality": "standard",
\    "size": "1024x1024",
\    "style": "vivid",
\    "request_timeout": 40,
\    "auth_type": "bearer",
\    "token_file_path": "",
\    "token_load_fn": "",
\  },
\  "ui": {
\    "download_dir": "",
\  },
\}

" custom roles file location
let g:vim_ai_roles_config_file = s:plugin_root . "/roles-example.ini"

" custom token file location
let g:vim_ai_token_file_path = "~/.config/openai.token"

" custom fn to load token, e.g. "g:GetAIToken()"
let g:vim_ai_token_load_fn = ""

" enable/disable asynchronous AIChat (enabled by default)
let g:vim_ai_async_chat = 1

" enables/disables full markdown highlighting in aichat files
" NOTE: code syntax highlighting works out of the box without this option enabled
" NOTE: highlighting may be corrupted when using together with the `preservim/vim-markdown`
g:vim_ai_chat_markdown = 0

" debug settings
let g:vim_ai_debug = 0
let g:vim_ai_debug_log_file = "/tmp/vim_ai_debug.log"

" Notes:
" ui.paste_mode
" - if disabled code indentation will work but AI doesn't always respond with a code block
"   therefore it could be messed up
" - find out more in vim's help `:help paste`
" options.max_tokens
" - note that prompt + max_tokens must be less than model's token limit, see #42, #46
" - setting max tokens to "" will exclude it from the OpenAI API request parameters, it is
"   unclear/undocumented what it exactly does, but it seems to resolve issues when the model
"   hits token limit, which respond with `OpenAI: HTTPError 400`
" options.selection_boundary
" - setting ``` value behaves in markdown-like fasion - adds filetype to the boundary

### Using custom API

It is possible to configure the plugin to use different OpenAI-compatible endpoints.
See some cool projects listed in [Custom APIs](https://github.com/madox2/vim-ai/wiki/Custom-APIs) section on the [Community Wiki](https://github.com/madox2/vim-ai/wiki).

```vim
let g:vim_ai_chat = {
\  "options": {
\    "endpoint_url": "http://localhost:8000/v1/chat/completions",
\    "auth_type": "none",
\  },
\}
```

#### Example: create custom roles to interact with OpenRouter models

First you need open an account on [OpenRouter](https://openrouter.ai/) website and create an api key.
You can start with [free models](https://openrouter.ai/models?max_price=0) and add credits later if you wish.
Then you set up a custom role that points to the OpenRouter endpoint:

```ini
[gemini]
options.token_file_path = ~/.config/openrouter.token
options.endpoint_url = https://openrouter.ai/api/v1/chat/completions
options.model = google/gemini-exp-1121:free

[llama]
options.token_file_path = ~/.config/openrouter.token
options.endpoint_url = https://openrouter.ai/api/v1/chat/completions
options.model = meta-llama/llama-3.3-70b-instruct

[claude]
options.token_file_path = ~/.config/openrouter.token
options.endpoint_url = https://openrouter.ai/api/v1/chat/completions
options.model = anthropic/claude-3.5-haiku
```

Now you can use the role:

```
:AI /gemini who created you?

I was created by Google.
```

## Key bindings

This plugin does not set any key binding. Create your own bindings in the `.vimrc` to trigger AI commands, for example:

```vim
" stop async chat generation
nnoremap <leader>s :AIStopChat<CR>

" complete text on the current line or in visual selection
nnoremap <leader>a :AI<CR>
xnoremap <leader>a :AI<CR>

" edit text with a custom prompt
xnoremap <leader>s :AIEdit fix grammar and spelling<CR>
nnoremap <leader>s :AIEdit fix grammar and spelling<CR>

" trigger chat
xnoremap <leader>c :AIChat<CR>
nnoremap <leader>c :AIChat<CR>

" redo last AI command
nnoremap <leader>r :AIRedo<CR>
```

## Custom commands

You might find useful a [collection](https://github.com/madox2/vim-ai/wiki/Custom-commands) of custom commands on the [Community Wiki](https://github.com/madox2/vim-ai/wiki).

To create a custom command, you can call `AIRun`, `AIEditRun` and `AIChatRun` functions. For example:

```vim
" custom command suggesting git commit message, takes no arguments
function! GitCommitMessageFn()
  let l:range = 0
  let l:diff = system('git --no-pager diff --staged')
  let l:prompt = "generate a short commit message from the diff below:\n" . l:diff
  let l:config = {
  \  "options": {
  \    "model": "gpt-4o",
  \    "initial_prompt": ">>> system\nyou are a code assistant",
  \    "temperature": 1,
  \  },
  \}
  call vim_ai#AIRun(l:range, l:config, l:prompt)
endfunction
command! GitCommitMessage call GitCommitMessageFn()


" custom command that provides a code review for selected code block
function! CodeReviewFn(range) range
  let l:prompt = "programming syntax is " . &filetype . ", review the code below"
  let l:config = {
  \  "options": {
  \    "initial_prompt": ">>> system\nyou are a clean code expert",
  \  },
  \}
  exe a:firstline.",".a:lastline . "call vim_ai#AIChatRun(a:range, l:config, l:prompt)"
endfunction
command! -range -nargs=? AICodeReview <line1>,<line2>call CodeReviewFn(<range>)
```

## Contributing

Contributions are welcome! Please feel free to open a pull request, report an issue, or contribute to the [Community Wiki](https://github.com/madox2/vim-ai/wiki).

## Important Disclaimer

**Accuracy**: GPT is good at producing text and code that looks correct at first glance, but may be completely wrong. Be sure to thoroughly review, read and test all output generated by this plugin!

**Privacy**: This plugin sends text to OpenAI (or other providers) when generating completions and edits. Therefore, do not use it on files containing sensitive information.

## License

[MIT License](https://github.com/madox2/vim-ai/blob/main/LICENSE)
