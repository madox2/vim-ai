# vim-ai

Complete text and chat with GPT in vim using OpenAI.

## Features

- Generate text or code, answer questions
- Edit selected text in-place
- Interactive conversation with ChatGPT

![vim-ai demo](./demo.gif)

## Installation

The plugin is compatible with Vim 8+ (tested on Debian). Windows OS is not supported yet.

```sh
# configure openai api key https://platform.openai.com/account/api-keys
echo "YOUR_OPENAI_API_KEY" > ~/.config/openai.token

# alternatively using environment variable
export OPENAI_API_KEY="YOUR_OPENAI_API_KEY"
```

Add plugin to your `.vimrc` using `vim-plug`:

```vim
Plug 'madox2/vim-ai', { 'do': './install.sh' }
```

The plugin requires `python3` and `pip3` to install and run [openai-python](https://github.com/openai/openai-python) library.

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

## Configuration

### Key bindings

Map keys in your `.vimrc` to trigger `:AI` command.

```vim
nnoremap <leader>a :AI<CR>
vnoremap <leader>a :AI<CR>
```

### Custom commands

To customize and re-use prompts it is useful to put some context to the language model. You can do it with prepending text to `:AI` command.

```vim
" key binding with custom context
vnoremap <leader>s :AIEdit fix grammar and spelling and use formal language<CR>
nnoremap <leader>s :AIEdit fix grammar and spelling and use formal language<CR>

" key binding to trigger chat
vnoremap <leader>c :AIChat <CR>
nnoremap <leader>c :AIChat <CR>

" command with custom context (vim-ai functions: AIRun, AIEditRun, AIChatRun)
command! -range -nargs=? AICode <line1>,<line2>call AIRun("Programming syntax is " . &filetype . ", " . <f-args>)
```


## Important Disclaimer

**Accuracy**: GPT is good at producing text and code that looks correct at first glance, but may be completely wrong. Be sure to thoroughly review, read and test all output generaged by this plugin!

**Privacy**: This plugin sends text to OpenAI when generating completions and edits. Therefore, do not use it on files containing sensitive information.

## License

[MIT License](https://github.com/madox2/vim-ai/blob/main/LICENSE)
