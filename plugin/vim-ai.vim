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
  let output = system("echo " . shellescape(prompt) . " | python3 " . s:complete_py . " ")
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
  let output = system("echo " . shellescape(prompt) . " | python3 " . s:complete_py . " ")
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
  let selection = trim(@*)
  let is_selection = lines != "" && lines == selection
  let has_instruction = a:0

  let prompt = ""
  if search('^>>> user$', 'nw') != 0
    " inside chat window
    let prompt = trim(join(getline(1, '$'), "\n"))
  else
    " outside chat window
    call ScratchWindow()
    if has_instruction
      if is_selection
        let prompt = a:1 . ":\n" . lines
      else
        let prompt = a:1
      endif
    else
      if is_selection
        let prompt = lines
      else
        execute "normal i>>> user\<Enter>\<Enter>"
        return
      endif
    endif
  endif

  if g:vim_ai_debug
    echo "Prompt:\n" . prompt . "\n"
  endif

  echo "Answering..."
  let output = system("echo " . shellescape(prompt) . " | python3 " . s:chat_py . " ")

  set paste
  execute "normal! ggdG"
  execute "normal! i" . output . "\<Esc>"
  set nopaste
endfunction

command! -range -nargs=? AI <line1>,<line2>call AIRun(<f-args>)
command! -range -nargs=? AIEdit <line1>,<line2>call AIEditRun(<f-args>)
command! -range -nargs=? AIChat <line1>,<line2>call AIChatRun(<f-args>)
