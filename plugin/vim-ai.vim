let s:plugin_root = expand('<sfile>:p:h:h')
let s:complete_py = s:plugin_root . "/py/complete.py"
let s:chat_py = s:plugin_root . "/py/chat.py"

if !exists('g:vim_ai_debug')
  let g:vim_ai_debug = 0
endif

function! ScratchWindow()
  below new
  setlocal buftype=nofile
  setlocal bufhidden=hide
  setlocal noswapfile
  setlocal ft=aichat
endfunction

function! AIRun(...) range
  let lines = trim(join(getline(a:firstline, a:lastline), "\n"))
  let selection = trim(@*)
  let is_selection = lines != "" && lines == selection
  let has_instruction = a:0
  let prompt = ""
  if has_instruction
    if is_selection
      let prompt = a:1 . ":\n" . lines
    else
      let prompt = a:1
    endif
  else
    let prompt = lines
  endif

  if g:vim_ai_debug
    echo "Prompt:\n" . prompt . "\n"
  endif
  echo "Completing..."
  " WORKAROUND: without sleep is echo on prev line not displayed (when combining with py3)
  execute 'silent sleep 1m'
  execute "py3file " . s:complete_py
  let output = py3eval('output')
  let output = trim(output)

  execute "normal! " . a:lastline . "G"
  set paste
  execute "normal! o" . output . "\<Esc>"
  set nopaste
  execute "normal! " . a:lastline . "G"
endfunction

function! AIEditRun(...) range
  let has_instruction = a:0
  let prompt = trim(join(getline(a:firstline, a:lastline), "\n"))
  if has_instruction
    let prompt = a:1 . ":\n" . prompt
  endif

  let buff_lastline = line('$')

  if g:vim_ai_debug
    echo "Prompt:\n" . prompt . "\n"
  endif

  echo "Editing..."
  " WORKAROUND: without sleep is echo on prev line not displayed (when combining with py3)
  execute 'silent sleep 1m'
  execute "py3file " . s:complete_py
  let output = py3eval('output')
  let output = trim(output)

  execute a:firstline . ',' . a:lastline . 'd'

  set paste
  if a:lastline == buff_lastline
    execute "normal! o" . output . "\<Esc>"
  else
    execute "normal! O" . output . "\<Esc>"
  endif
  set nopaste
endfunction

function! AIChatRun(...) range
  let lines = trim(join(getline(a:firstline, a:lastline), "\n"))
  let is_selection = lines != "" && lines == trim(@*)
  let instruction = a:0 ? trim(a:1) : ""

  set paste
  if search('^>>> user$', 'nw') == 0
    " outside of chat window
    call ScratchWindow()
    let delimiter = instruction != "" && is_selection ? ":\n" : ""
    let selection = is_selection ? lines : ""
    let prompt = join([instruction, delimiter, selection], "")
    execute "normal i>>> user\<Enter>\<Enter>" . prompt
    if prompt == ""
      " empty prompt, just opens chat window TODO: handle in python
      return
    endif
  endif

  echo "Answering..."
  execute "py3file " . s:chat_py
  set nopaste
endfunction

command! -range -nargs=? AI <line1>,<line2>call AIRun(<f-args>)
command! -range -nargs=? AIEdit <line1>,<line2>call AIEditRun(<f-args>)
command! -range -nargs=? AIChat <line1>,<line2>call AIChatRun(<f-args>)
