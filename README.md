# vim-ai

This plugin adds Artificial Intelligence (AI) capabilities to your Vim and Neovim.
You can generate code, edit text, or have an interactive conversation with GPT models, all powered by OpenAI's API.

## Features

- Generate text or code, answer questions with AI
- Edit selected text in-place with AI
- Interactive conversation with ChatGPT

![vim-ai demo](./demo.gif)

## Installation

vim-ai requires Vim/Neovim compiled with python3 support and the [openai-python](https://github.com/openai/openai-python) library (version 0.27+).

```sh
# configure openai api key https://platform.openai.com/account/api-keys
echo "YOUR_OPENAI_API_KEY" > ~/.config/openai.token

# alternatively using environment variable
export OPENAI_API_KEY="YOUR_OPENAI_API_KEY"
```

Add plugin to your `.vimrc` using `vim-plug`:

```vim
" ./install.sh script will automatically install openai-python
Plug 'madox2/vim-ai', { 'do': './install.sh' }
```

Alternatively, you can install manually like so:
```
git clone https://github.com/madox2/vim-ai/
mv vim-ai ~/.config/nvim/plugin/  # this is an example, use your own appropriate path
```

## Usage

### :AI

`:AI` - complete the text on the current line

`:AI {prompt}` - complete the prompt

`(visual selection) :AI` - complete the selection

`(visual selection) :AI {instruction}` - complete the selection using the instruction

### :AIEdit

`(visual selection)? :AIEdit` - edit the current line or the selection

`(visual selection)? :AIEdit {instruction}` - edit the current line or the selection using the instruction

### :AIChat

`:AIChat` - continue or start a new conversation.

`(visual selection)? :AIChat {instruction}?` - start a new conversation given the selection, the instruction or both

Press `Ctrl-c` to cancel completion.

When the AI finished answering, you can continue the conversation by entering edit mode, adding your prompt then using the command `:AIChat` once again.

#### Custom conversation prompts

You can edit and save the conversation to an `.aichat` file and restore it later.
This allows you to create re-usable custom prompts. For example:

```
# ./refactoring-prompt.aichat

>>> system

You are a Clean Code expert, I have the following code, please refactor it in a more clean and concise way so that my colleagues can maintain the code more easily. Also, explain why you want to refactor the code so that I can add the explanation to the Pull Request.

>>> user

[attach code]

```

Supported chat roles are **`>>> system`**, **`>>> user`** and **`<<< assistant`**

### :AIRedo

`:AIRedo` - repeat last AI command

Use this immediately after `AI`/`AIEdit`/`AIChat` command in order to re-try or get an alternative completion.
Note that the randomness of responses heavily depends on the [`temperature`](https://platform.openai.com/docs/api-reference/completions/create#completions/create-temperature) parameter.

## Configuration

### Key bindings

Map keys in your `.vimrc` to trigger `:AI` command.

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

### Interface configuration

Default interface configuration:

```vim
let g:vim_ai_chat = {
\  "ui": {
\    "open_chat_command": "below new | call vim_ai#MakeScratchWindow()",
\    "code_syntax_enabled": 1,
\  },
\}
```

Tips:

```vim
" restore conversation from the file
let g:vim_ai_chat = {
\  "ui": {
\    "open_chat_command": "below new /tmp/last_conversation.aichat",
\  },
\}

" open chat in a new tab
let g:vim_ai_chat = {
\  "ui": {
\    "open_chat_command": "tabnew | call vim_ai#MakeScratchWindow()",
\  },
\}
```

### Completion configuration

Request to the OpenAI API can be configured for each command.
To customize the default configuration, initialize the config variable with a selection of options.  For example:

```vim
let g:vim_ai_chat = {
\  "options": {
\    "model": "gpt-4",
\    "temperature": 0.2,
\  },
\}
```

Below are listed available options along with default values:

```vim
" :AI
" - https://platform.openai.com/docs/api-reference/completions
" - see how to configure chat engine for completion in the section below
let g:vim_ai_complete = {
\  "engine": "complete",
\  "options": {
\    "model": "text-davinci-003",
\    "max_tokens": 1000,
\    "temperature": 0.1,
\    "request_timeout": 10,
\  },
\}

" :AIEdit
" - https://platform.openai.com/docs/api-reference/completions
" - see how to configure chat engine for edits in the section below
let g:vim_ai_edit = {
\  "engine": "complete",
\  "options": {
\    "model": "text-davinci-003",
\    "max_tokens": 1000,
\    "temperature": 0.1,
\    "request_timeout": 10,
\  },
\}

" :AIChat
" - https://platform.openai.com/docs/api-reference/chat
let g:vim_ai_chat = {
\  "options": {
\    "model": "gpt-3.5-turbo",
\    "max_tokens": 1000,
\    "temperature": 1,
\    "request_timeout": 10,
\    "initial_prompt": "",
\  },
\}
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
let g:vim_ai_complete = chat_engine_config
```

### Custom commands

To customize and re-use prompts it is useful to put some context in it. You can do it by prepending text to AI commands.

```vim
command! -range -nargs=? AITranslate <line1>,<line2>call AIEditRun(<range>, "Translate to English: " . <q-args>)

command! -range -nargs=? AICode <line1>,<line2>call AIRun(<range>, "Programming syntax is " . &filetype . ", " . <q-args>)

" available functions are: AIRun, AIEditRun, AIChatRun
```


## Important Disclaimer

**Accuracy**: GPT is good at producing text and code that looks correct at first glance, but may be completely wrong. Be sure to thoroughly review, read and test all output generated by this plugin!

**Privacy**: This plugin sends text to OpenAI when generating completions and edits. Therefore, do not use it on files containing sensitive information.

## License

[MIT License](https://github.com/madox2/vim-ai/blob/main/LICENSE)
