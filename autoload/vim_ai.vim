" Add ChatGPT dependencies
python3 << EOF
import sys
try:
    import openai
except ImportError:
    print("Error: OpenAI module not found. Please install with Pip and ensure equality of the versions given by :!python3 -V, and :python3 import sys; print(sys.version)")
    raise
import vim
import os
EOF


function! vim_ai#MakeScratchWindow()
  setlocal buftype=nofile
  setlocal bufhidden=hide
  setlocal noswapfile
  setlocal ft=aichat
endfunction

function! s:MakePrompt(is_selection, lines, instruction)
  let lines = trim(join(a:lines, "\n"))
  let instruction = trim(a:instruction)
  let delimiter = instruction != "" && a:is_selection ? ":\n" : ""
  let selection = a:is_selection || instruction == "" ? lines : ""
  let prompt = join([instruction, delimiter, selection], "")
  return prompt
endfunction

function! vim_ai#Run(is_selection, ...) range
  let instruction = a:0 ? a:1 : ""
  let lines = getline(a:firstline, a:lastline)
  let prompt = s:MakePrompt(a:is_selection, lines, instruction)

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

function! vim_ai#EditRun(is_selection, ...) range
  let instruction = a:0 ? a:1 : ""
  let prompt = s:MakePrompt(a:is_selection, getline(a:firstline, a:lastline), instruction)

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

function! vim_ai#ChatRun(is_selection, ...) range
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
      let prompt = s:MakePrompt(a:is_selection, lines, instruction)
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

function! vim_ai#RedoRun()
  execute "normal! u"
  if s:last_command == "complete"
    if s:last_is_selection
      '<,'>call vim_ai#Run(s:last_is_selection, s:last_instruction)
    else
      call vim_ai#Run(s:last_is_selection, s:last_instruction)
    endif
  endif
  if s:last_command == "edit"
    if s:last_is_selection
      '<,'>call vim_ai#EditRun(s:last_is_selection, s:last_instruction)
    else
      call vim_ai#EditRun(s:last_is_selection, s:last_instruction)
    endif
  endif
  if s:last_command == "chat"
    call vim_ai#ChatRun(s:last_is_selection, s:last_instruction)
  endif
endfunction
