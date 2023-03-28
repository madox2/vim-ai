let g:vim_ai_complete_default = {
\  "options": {
\    "model": "text-davinci-003",
\    "max_tokens": 1000,
\    "temperature": 0.1,
\    "request_timeout": 20,
\  },
\}
let g:vim_ai_edit_default = {
\  "options": {
\    "model": "text-davinci-003",
\    "max_tokens": 1000,
\    "temperature": 0.1,
\    "request_timeout": 20,
\  },
\}
let g:vim_ai_chat_default = {
\  "options": {
\    "model": "gpt-3.5-turbo",
\    "max_tokens": 1000,
\    "temperature": 1,
\    "request_timeout": 20,
\  },
\}
if !exists('g:vim_ai_complete')
  let g:vim_ai_complete = {"options":{}}
endif
if !exists('g:vim_ai_edit')
  let g:vim_ai_edit = {"options":{}}
endif
if !exists('g:vim_ai_chat')
  let g:vim_ai_chat = {"options":{}}
endif


let s:plugin_root = expand('<sfile>:p:h:h')
let s:complete_py = s:plugin_root . "/py/complete.py"
let s:chat_py = s:plugin_root . "/py/chat.py"

" remembers last command parameters to be used in AIRedoRun
let s:last_is_selection = 0
let s:last_instruction = ""
let s:last_command = ""

function! ScratchWindow()
  below new
  setlocal buftype=nofile
  setlocal bufhidden=hide
  setlocal noswapfile
  setlocal ft=aichat
endfunction

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

  let options_default = g:vim_ai_complete_default['options']
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

  let options_default = g:vim_ai_edit_default['options']
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
    call ScratchWindow()
    let prompt = ""
    if a:0 || a:is_selection
      let instruction = a:0 ? a:1 : ""
      let prompt = MakePrompt(a:is_selection, lines, instruction)
    endif
    execute "normal! i>>> user\n\n" . prompt
  endif

  let s:last_command = "chat"
  let s:last_instruction = instruction
  let s:last_is_selection = a:is_selection

  let options_default = g:vim_ai_chat_default['options']
  let options = g:vim_ai_chat['options']
  execute "py3file " . s:chat_py
  set nopaste
endfunction

function! AIRedoRun()
  execute "normal! u"
  if s:last_command == "complete"
    '<,'>call AIRun(s:last_is_selection, s:last_instruction)
  endif
  if s:last_command == "edit"
    '<,'>call AIEditRun(s:last_is_selection, s:last_instruction)
  endif
  if s:last_command == "chat"
    call AIChatRun(s:last_is_selection, s:last_instruction)
  endif
endfunction

command! -range -nargs=? AI <line1>,<line2>call AIRun(<range>, <f-args>)
command! -range -nargs=? AIEdit <line1>,<line2>call AIEditRun(<range>, <f-args>)
command! -range -nargs=? AIChat <line1>,<line2>call AIChatRun(<range>, <f-args>)
command! AIRedo call AIRedoRun()
