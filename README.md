# vim-ai

Complete text in vim using OpenAI.

![vim-ai demo](./demo.gif)

## Installation

Prerequisites:

```sh
# configure openai api key https://platform.openai.com/account/api-keys
echo "YOUR_OPENAPI_TOKEN" > ~/.config/openai.token

# alternatively using environment variable
export OPENAI_API_TOKEN="YOUR_OPENAPI_TOKEN"
```

Add plugin to your `.vimrc` using `vim-plug`:

```vim
Plug 'madox2/vim-ai', { 'do': './install.sh' }
```

The plugin requires `python3` and `pip3` to be installed.

## Usage

### Basic usage

`:AI {prompt}` - completes selected text (visual mode) or text on the current line (normal mode). Passing optional `{prompt}` parameter prepends it to the final prompt.

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
vnoremap <leader>s :AI fix grammar and spelling and use formal language<CR>
nnoremap <leader>s :AI fix grammar and spelling and use formal language<CR>

" command with custom context
command! -range -nargs=? AICode <line1>,<line2>call AIRun("Programming syntax is " . &filetype, <f-args>)
```


## Important Disclaimer

**Accuracy**: GPT is good at producing text and code that looks correct at first glance, but may be completely wrong. Be sure to thoroughly review, read and test all output generaged by this plugin!

**Privacy**: This plugin sends text to OpenAI when generating completions and edits. Therefore, do not use it on files containing sensitive information.

## License

[MIT License](https://github.com/madox2/vim-ai/blob/main/LICENSE)
