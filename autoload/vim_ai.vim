call vim_ai_config#load()

let s:plugin_root = expand('<sfile>:p:h:h')
let s:complete_py = s:plugin_root . "/py/complete.py"
let s:chat_py = s:plugin_root . "/py/chat.py"

" remembers last command parameters to be used in AIRedoRun
let s:last_is_selection = 0
let s:last_instruction = ""
let s:last_command = ""

" Configures ai-chat scratch window.
" - scratch_buffer_keep_open = 0
"   - opens new ai-chat every time
" - scratch_buffer_keep_open = 1
"   - opens last ai-chat buffer
"   - keeps the buffer in the buffer list
function! vim_ai#MakeScratchWindow()
  let l:keep_open = g:vim_ai_chat['ui']['scratch_buffer_keep_open']
  if l:keep_open && bufexists("[AI chat]")
    " reuse chat buffer
    buffer \[AI chat\]
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
  if bufexists("[AI chat]")
    " spawn another window if chat already exist
    let l:index = 2
    while bufexists("[AI chat " . l:index . "]")
      let l:index += 1
    endwhile
    execute "file [AI chat ". l:index . "]"
  else
    file [AI chat]
  endif
endfunction

function! MakePrompt(is_selection, lines, instruction)
  let lines = trim(join(a:lines, "\n"))
  let instruction = trim(a:instruction)
  let delimiter = instruction != "" && a:is_selection ? ":\n" : ""
  let selection = a:is_selection || instruction == "" ? lines : ""
  let prompt = join([instruction, delimiter, selection], "")
  return prompt
endfunction

function! vim_ai#AIRun(is_selection, ...) range
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

function! vim_ai#AIEditRun(is_selection, ...) range
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

function! vim_ai#AIChatRun(is_selection, ...) range
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
