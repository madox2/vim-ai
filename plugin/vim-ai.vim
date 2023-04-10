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
\    "code_syntax_enabled": 1,
\    "populate_options": 0,
\  },
\}

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

function! MakePrompt(is_selection, lines, instruction)
  let lines = trim(join(a:lines, "\n"))
  let instruction = trim(a:instruction)
  let delimiter = instruction != "" && a:is_selection ? ":\n" : ""
  let selection = a:is_selection || instruction == "" ? lines : ""
  let prompt = join([instruction, delimiter, selection], "")
  return prompt
endfunction

function! AIRun(is_selection, ...) range
  let instruction = a:0 ? a:1 : ""
  let lines = getline(a:firstline, a:lastline)
  let prompt = MakePrompt(a:is_selection, lines, instruction)

  let s:last_command = "complete"
  let s:last_instruction = instruction
  let s:last_is_selection = a:is_selection

  let engine = g:vim_ai_complete['engine']
  let options = g:vim_ai_complete['options']
  let cursor_on_empty_line = trim(join(lines, "\n")) == ""
  set paste
  if cursor_on_empty_line
    execute "normal! " . a:lastline . "GA"
  else
    execute "normal! " . a:lastline . "Go"
  endif
  execute "py3file " . s:complete_py
  execute "normal! " . a:lastline . "G"
  set nopaste
endfunction

function! AIEditRun(is_selection, ...) range
  let instruction = a:0 ? a:1 : ""
  let prompt = MakePrompt(a:is_selection, getline(a:firstline, a:lastline), instruction)

  let s:last_command = "edit"
  let s:last_instruction = instruction
  let s:last_is_selection = a:is_selection

  let engine = g:vim_ai_edit['engine']
  let options = g:vim_ai_edit['options']
  set paste
  execute "normal! " . a:firstline . "GV" . a:lastline . "Gc"
  execute "py3file " . s:complete_py
  set nopaste
endfunction

function! AIChatRun(is_selection, ...) range
  let instruction = ""
  let lines = getline(a:firstline, a:lastline)
  set paste
  let is_outside_of_chat_window = search('^>>> user$', 'nw') == 0
  if is_outside_of_chat_window
    " open chat window
    execute g:vim_ai_chat['ui']['open_chat_command']
    let prompt = ""
    if a:0 || a:is_selection
      let instruction = a:0 ? a:1 : ""
      let prompt = MakePrompt(a:is_selection, lines, instruction)
    endif
    execute "normal! Gi" . prompt
  endif

  let s:last_command = "chat"
  let s:last_instruction = instruction
  let s:last_is_selection = a:is_selection

  let options = g:vim_ai_chat['options']
  let ui = g:vim_ai_chat['ui']
  execute "py3file " . s:chat_py
  set nopaste
endfunction

function! AIRedoRun()
  execute "normal! u"
  if s:last_command == "complete"
    if s:last_is_selection
      '<,'>call AIRun(s:last_is_selection, s:last_instruction)
    else
      call AIRun(s:last_is_selection, s:last_instruction)
    endif
  endif
  if s:last_command == "edit"
    if s:last_is_selection
      '<,'>call AIEditRun(s:last_is_selection, s:last_instruction)
    else
      call AIEditRun(s:last_is_selection, s:last_instruction)
    endif
  endif
  if s:last_command == "chat"
    call AIChatRun(s:last_is_selection, s:last_instruction)
  endif
endfunction

command! -range -nargs=? AI <line1>,<line2>call AIRun(<range>, <f-args>)
command! -range -nargs=? AIEdit <line1>,<line2>call AIEditRun(<range>, <f-args>)
command! -range -nargs=? AIChat <line1>,<line2>call AIChatRun(<range>, <f-args>)
command! AIRedo call AIRedoRun()
