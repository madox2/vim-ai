# vim-ai

This plugin adds Artificial Intelligence (AI) capabilities to your Vim and Neovim.
You can generate code, edit text, or have an interactive conversation with GPT models, all powered by OpenAI's API.

![vim-ai demo](./demo.gif)

## Features

- Generate text or code, answer questions with AI
- Edit selected text in-place with AI
- Interactive conversation with ChatGPT

## Installation

### Prerequisites

- Vim or Neovim compiled with python3 support
- Setup [OpenAI API key](https://platform.openai.com/account/api-keys)

```sh
# save api key to `~/.config/openai.token` file
echo "YOUR_OPENAI_API_KEY" > ~/.config/openai.token

# alternatively set it as an environment variable
export OPENAI_API_KEY="YOUR_OPENAI_API_KEY"
```

### Using `vim-plug`

```vim
Plug 'madox2/vim-ai'
```

### Manual installation

```sh
git clone https://github.com/madox2/vim-ai/
mv vim-ai ~/.config/nvim/plugin/  # copy to the plugin directory
```

## Usage

### Getting started

To use an AI command, type the command followed by an instruction prompt `{instruction}`. You can also combine it with a visual selection `<selection>`. Here is a brief overview of available commands:

```
:AI         complete text
:AIEdit     edit text
:AIChat     open/continue chat
:AIRedo     repeat last AI command

:help vim-ai
```
In the documentation below, the `?` symbol denotes an optional parameter.

**Tip:** Press `Ctrl-c` anytime to cancel completion

**Tip:** setup your own [key bindings](#key-bindings) or use command shortcuts - `:AIE`, `:AIC`, `:AIR`

### `:AI`

`:AI` - complete the text on the current line

`:AI {prompt}` - complete the prompt

`<selection> :AI` - complete the selection

`<selection> :AI {instruction}` - complete the selection using the instruction

### `:AIEdit`

`<selection>? :AIEdit` - edit the current line or the selection

`<selection>? :AIEdit {instruction}` - edit the current line or the selection using the instruction

### `:AIChat`

`:AIChat` - continue or start a new conversation.

`<selection>? :AIChat {instruction}?` - start a new conversation given the selection, the instruction or both

When the AI finishes answering, you can continue the conversation by entering insert mode, adding your prompt, and then using the command `:AIChat` once again.

### `:AIRedo`

`:AIRedo` - repeat last AI command

Use this immediately after `AI`/`AIEdit`/`AIChat` command in order to re-try or get an alternative completion.
Note that the randomness of responses heavily depends on the [`temperature`](https://platform.openai.com/docs/api-reference/completions/create#completions/create-temperature) parameter.

### `.aichat` files

You can edit and save the chat conversation to an `.aichat` file and restore it later.
This allows you to create re-usable custom prompts, for example:

```
# ./refactoring-prompt.aichat

>>> system

You are a Clean Code expert, I have the following code, please refactor it in a more clean and concise way so that my colleagues can maintain the code more easily. Also, explain why you want to refactor the code so that I can add the explanation to the Pull Request.

>>> user

[attach code]

```

Supported chat roles are **`>>> system`**, **`>>> user`** and **`<<< assistant`**

## Key bindings

This plugin does not set any key binding. Create your own bindings in the `.vimrc` to trigger AI commands, for example:

```vim
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

## Configuration

Each command is configured with a corresponding configuration variable.
To customize the default configuration, initialize the config variable with a selection of options, for example:

```vim
let g:vim_ai_chat = {
\  "options": {
\    "model": "gpt-4",
\    "temperature": 0.2,
\  },
\}
```

Or modify options directly during the vim session:

```vim
let g:vim_ai_chat['options']['model'] = 'gpt-4'
let g:vim_ai_chat['options']['temperature'] = 0.2
```

You can also customize the options in the chat header:

```properties
[chat-options]
model=gpt-4
temperature=0.2

>>> user

generate a paragraph of lorem ipsum
```

Below are listed all available configuration options, along with their default values:

```vim
" :AI
" - options: openai config (see https://platform.openai.com/docs/api-reference/completions)
" - engine: complete | chat - see how to configure chat engine in the section below
let g:vim_ai_complete = {
\  "engine": "complete",
\  "options": {
\    "model": "text-davinci-003",
\    "max_tokens": 1000,
\    "temperature": 0.1,
\    "request_timeout": 20,
\  },
\}

" :AIEdit
" - options: openai config (see https://platform.openai.com/docs/api-reference/completions)
" - engine: complete | chat - see how to configure chat engine in the section below
let g:vim_ai_edit = {
\  "engine": "complete",
\  "options": {
\    "model": "text-davinci-003",
\    "max_tokens": 1000,
\    "temperature": 0.1,
\    "request_timeout": 20,
\  },
\}

" This prompt instructs model to work with syntax highlighting
let s:initial_chat_prompt =<< trim END
>>> system

You are a general assistant.
If you attach a code block add syntax type after ``` to enable syntax highlighting.
END

" :AIChat
" - options: openai config (see https://platform.openai.com/docs/api-reference/chat)
" - options.initial_prompt: prompt prepended to every chat request
" - ui.populate_options: put [chat-options] to the chat header
" - ui.open_chat_command: customize how to open chat window
let g:vim_ai_chat = {
\  "options": {
\    "model": "gpt-3.5-turbo",
\    "max_tokens": 1000,
\    "temperature": 1,
\    "request_timeout": 20,
\    "initial_prompt": s:initial_chat_prompt,
\  },
\  "ui": {
\    "code_syntax_enabled": 1,
\    "populate_options": 0,
\    "open_chat_command": "below new | call vim_ai#MakeScratchWindow()",
\  },
\}

" Tips:
" "open_chat_command":
" - "below new /tmp/last_conversation.aichat" - restore converstaion from a file
" - "open_chat_command": "tabnew | call vim_ai#MakeScratchWindow()" - open chat in a new tab
```

### Using chat engine for completion and edits

It is possible to configure chat models, such as `gpt-3.5-turbo`, to be used in `:AI` and `:AIEdit` commands.
These models are cheaper, but currently less suitable for code editing/completion, as they respond with human-like text and commentary.

Depending on the use case, a good initial prompt can help to instruct the chat model to respond in the desired way:

```vim
let initial_prompt =<< trim END
>>> system

You are going to play a role of a completion engine with following parameters:
Task: Provide compact code/text completion, generation, transformation or explanation
Topic: general programming and text editing
Style: Plain result without any commentary, unless commentary is necessary
Audience: Users of text editor and programmers that need to transform/generate text
END

let chat_engine_config = {
\  "engine": "chat",
\  "options": {
\    "model": "gpt-3.5-turbo",
\    "max_tokens": 1000,
\    "temperature": 0.1,
\    "request_timeout": 20,
\    "initial_prompt": initial_prompt,
\  },
\}

let g:vim_ai_complete = chat_engine_config
let g:vim_ai_edit = chat_engine_config
```

## Important Disclaimer

**Accuracy**: GPT is good at producing text and code that looks correct at first glance, but may be completely wrong. Be sure to thoroughly review, read and test all output generated by this plugin!

**Privacy**: This plugin sends text to OpenAI when generating completions and edits. Therefore, do not use it on files containing sensitive information.

## License

[MIT License](https://github.com/madox2/vim-ai/blob/main/LICENSE)
