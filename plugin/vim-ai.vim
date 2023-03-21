let g:vim_ai_complete = {
\  "options": {
\    "model": "text-davinci-003",
\    "max_tokens": 1000,
\    "temperature": 0.1,
\    "request_timeout": 10,
\  },
\}
let g:vim_ai_edit = {
\  "options": {
\    "model": "text-davinci-003",
\    "max_tokens": 1000,
\    "temperature": 0.1,
\    "request_timeout": 10,
\  },
\}
let g:vim_ai_chat = {
\  "options": {
\    "model": "gpt-3.5-turbo",
\    "max_tokens": 1000,
\    "temperature": 1,
\    "request_timeout": 10,
\  },
\}

let s:plugin_root = expand('<sfile>:p:h:h')
let s:complete_py = s:plugin_root . "/py/complete.py"
let s:chat_py = s:plugin_root . "/py/chat.py"

function! ScratchWindow()
  below new
  setlocal buftype=nofile
  setlocal bufhidden=hide
  setlocal noswapfile
  setlocal ft=aichat
endfunction

function! MakePrompt(lines, instruction)
  let lines = trim(join(a:lines, "\n"))
  let is_selection = lines != "" && lines == trim(@*)
  let instruction = trim(a:instruction)
  let delimiter = instruction != "" && is_selection ? ":\n" : ""
  let selection = is_selection ? lines : ""
  let prompt = join([instruction, delimiter, selection], "")
  return prompt
endfunction

function! AIRun(...) range
  let prompt = MakePrompt(getline(a:firstline, a:lastline), a:0 ? a:1 : "")
  let options = g:vim_ai_complete['options']
  set paste
  execute "normal! " . a:lastline . "Go"
  execute "py3file " . s:complete_py
  execute "normal! " . a:lastline . "G"
  set nopaste
endfunction

function! AIEditRun(...) range
  let prompt = MakePrompt(getline(a:firstline, a:lastline), a:0 ? a:1 : "")
  let options = g:vim_ai_edit['options']
  set paste
  execute "normal! " . a:firstline . "GV" . a:lastline . "Gc"
  execute "py3file " . s:complete_py
  set nopaste
endfunction

function! AIChatRun(...) range
  let lines = getline(a:firstline, a:lastline)
  set paste
  let is_outside_of_chat_window = search('^>>> user$', 'nw') == 0
  if is_outside_of_chat_window
    call ScratchWindow()
    let prompt = MakePrompt(lines, a:0 ? a:1 : "")
    execute "normal i>>> user\n\n" . prompt
  endif

  let options = g:vim_ai_chat['options']
  execute "py3file " . s:chat_py
  set nopaste
endfunction

command! -range -nargs=? AI <line1>,<line2>call AIRun(<f-args>)
command! -range -nargs=? AIEdit <line1>,<line2>call AIEditRun(<f-args>)
command! -range -nargs=? AIChat <line1>,<line2>call AIChatRun(<f-args>)
