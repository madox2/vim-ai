call vim_ai_config#load()

let s:plugin_root = expand('<sfile>:p:h:h')
let s:complete_py = s:plugin_root . "/py/complete.py"
let s:chat_py = s:plugin_root . "/py/chat.py"

" remembers last command parameters to be used in AIRedoRun
let s:last_is_selection = 0
let s:last_instruction = ""
let s:last_command = ""

let s:scratch_buffer_name = ">>> AI chat"

" Configures ai-chat scratch window.
" - scratch_buffer_keep_open = 0
"   - opens new ai-chat every time
" - scratch_buffer_keep_open = 1
"   - opens last ai-chat buffer
"   - keeps the buffer in the buffer list
function! vim_ai#MakeScratchWindow()
  let l:keep_open = g:vim_ai_chat['ui']['scratch_buffer_keep_open']
  if l:keep_open && bufexists(s:scratch_buffer_name)
    " reuse chat buffer
    execute "buffer " . s:scratch_buffer_name
    return
  endif
  setlocal buftype=nofile
  setlocal noswapfile
  setlocal ft=aichat
  if l:keep_open
    setlocal bufhidden=hide
  else
    setlocal bufhidden=wipe
  endif
  if bufexists(s:scratch_buffer_name)
    " spawn another window if chat already exist
    let l:index = 2
    while bufexists(s:scratch_buffer_name . " " . l:index)
      let l:index += 1
    endwhile
    execute "file " . s:scratch_buffer_name . " " . l:index
  else
    execute "file " . s:scratch_buffer_name
  endif
endfunction

function! s:MakePrompt(is_selection, lines, instruction)
  let l:lines = trim(join(a:lines, "\n"))
  let l:instruction = trim(a:instruction)
  let l:delimiter = l:instruction != "" && a:is_selection ? ":\n" : ""
  let l:selection = ""
  if l:instruction == ""
    let l:selection = l:lines
  elseif a:is_selection
    " NOTE: surround selection with ##### in order to eliminate empty responses
    " TODO: add selection prompt boundary config
    if match(l:lines, "#####") != -1
      let l:selection = l:lines
    else
      let l:selection = "#####\n" . l:lines . "\n#####"
    endif
  endif
  return join([l:instruction, l:delimiter, l:selection], "")
endfunction

function! vim_ai#AIRun(is_selection, ...) range
  let l:instruction = a:0 ? a:1 : ""
  let l:lines = getline(a:firstline, a:lastline)
  let l:prompt = s:MakePrompt(a:is_selection, l:lines, l:instruction)

  let s:last_command = "complete"
  let s:last_instruction = l:instruction
  let s:last_is_selection = a:is_selection

  let l:engine = g:vim_ai_complete['engine']
  let l:options = g:vim_ai_complete['options']
  let l:cursor_on_empty_line = trim(join(l:lines, "\n")) == ""
  set paste
  if l:cursor_on_empty_line
    execute "normal! " . a:lastline . "GA"
  else
    execute "normal! " . a:lastline . "Go"
  endif
  execute "py3file " . s:complete_py
  execute "normal! " . a:lastline . "G"
  set nopaste
endfunction

function! vim_ai#AIEditRun(is_selection, ...) range
  let l:instruction = a:0 ? a:1 : ""
  let l:prompt = s:MakePrompt(a:is_selection, getline(a:firstline, a:lastline), l:instruction)

  let s:last_command = "edit"
  let s:last_instruction = l:instruction
  let s:last_is_selection = a:is_selection

  let l:engine = g:vim_ai_edit['engine']
  let l:options = g:vim_ai_edit['options']
  set paste
  execute "normal! " . a:firstline . "GV" . a:lastline . "Gc"
  execute "py3file " . s:complete_py
  set nopaste
endfunction

function! vim_ai#AIChatRun(is_selection, ...) range
  let l:instruction = ""
  let l:lines = getline(a:firstline, a:lastline)
  set paste
  if &filetype != 'aichat'
    " open chat window
    execute g:vim_ai_chat['ui']['open_chat_command']
    let l:prompt = ""
    if a:0 || a:is_selection
      let l:instruction = a:0 ? a:1 : ""
      let l:prompt = s:MakePrompt(a:is_selection, l:lines, l:instruction)
    endif
    execute "normal! Gi" . l:prompt
  endif

  let s:last_command = "chat"
  let s:last_instruction = l:instruction
  let s:last_is_selection = a:is_selection

  let l:options = g:vim_ai_chat['options']
  let l:ui = g:vim_ai_chat['ui']
  execute "py3file " . s:chat_py
  set nopaste
endfunction

function! vim_ai#AIRedoRun()
  execute "normal! u"
  if s:last_command == "complete"
    if s:last_is_selection
      '<,'>call vim_ai#AIRun(s:last_is_selection, s:last_instruction)
    else
      call vim_ai#AIRun(s:last_is_selection, s:last_instruction)
    endif
  endif
  if s:last_command == "edit"
    if s:last_is_selection
      '<,'>call vim_ai#AIEditRun(s:last_is_selection, s:last_instruction)
    else
      call vim_ai#AIEditRun(s:last_is_selection, s:last_instruction)
    endif
  endif
  if s:last_command == "chat"
    call vim_ai#AIChatRun(s:last_is_selection, s:last_instruction)
  endif
endfunction
