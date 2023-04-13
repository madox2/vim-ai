if !has('python3')
  echoerr "Python 3 support is required for vim-ai plugin"
  finish
endif

let g:vim_ai_complete_default = {
\  "engine": "complete",
\  "options": {
\    "model": "text-davinci-003",
\    "max_tokens": 1000,
\    "temperature": 0.1,
\    "request_timeout": 20,
\  },
\}
let g:vim_ai_edit_default = {
\  "engine": "complete",
\  "options": {
\    "model": "text-davinci-003",
\    "max_tokens": 1000,
\    "temperature": 0.1,
\    "request_timeout": 20,
\  },
\}

let s:initial_chat_prompt =<< trim END
>>> system

You are a general assistant.
If you attach a code block add syntax type after ``` to enable syntax highlighting.
END
let g:vim_ai_chat_default = {
\  "options": {
\    "model": "gpt-3.5-turbo",
\    "max_tokens": 1000,
\    "temperature": 1,
\    "request_timeout": 20,
\    "initial_prompt": s:initial_chat_prompt,
\  },
\  "ui": {
\    "open_chat_command": "below new | call vim_ai#MakeScratchWindow()",
\    "populate_options": 0,
\    "code_syntax_enabled": 1,
\  },
\}

if !exists("g:vim_ai_debug")
  let g:vim_ai_debug = 0
endif

if !exists("g:vim_ai_debug_log_file")
  let g:vim_ai_debug_log_file = "/tmp/vim_ai_debug.log"
endif

function! s:ExtendDeep(defaults, override) abort
  let l:result = a:defaults
  for [l:key, l:value] in items(a:override)
    if type(get(l:result, l:key)) is v:t_dict && type(l:value) is v:t_dict
      call s:ExtendDeep(l:result[l:key], l:value)
    else
      let l:result[l:key] = l:value
    endif
  endfor
  return l:result
endfun

function! s:MakeConfig(config_name) abort
  let l:defaults = copy(g:[a:config_name . "_default"])
  let l:override = exists("g:" . a:config_name) ? g:[a:config_name] : {}
  let g:[a:config_name] = s:ExtendDeep(l:defaults, l:override)
endfun

call s:MakeConfig("vim_ai_chat")
call s:MakeConfig("vim_ai_complete")
call s:MakeConfig("vim_ai_edit")

let s:plugin_root = expand('<sfile>:p:h:h')
let s:complete_py = s:plugin_root . "/py/complete.py"
let s:chat_py = s:plugin_root . "/py/chat.py"

" remembers last command parameters to be used in AIRedoRun
let s:last_is_selection = 0
let s:last_instruction = ""
let s:last_command = ""

command! -range -nargs=? AI <line1>,<line2>call vim_ai#Run(<range>, <f-args>)
command! -range -nargs=? AIEdit <line1>,<line2>call vim_ai#EditRun(<range>, <f-args>)
command! -range -nargs=? AIChat <line1>,<line2>call vim_ai#ChatRun(<range>, <f-args>)
command! AIRedo call vim_ai#RedoRun()
