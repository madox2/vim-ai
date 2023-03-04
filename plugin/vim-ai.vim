let s:plugin_root = expand('<sfile>:p:h:h')
let s:complete_py = s:plugin_root . "/py/complete.py"
let s:chat_py = s:plugin_root . "/py/chat.py"

function! ScratchWindow()
  below new
  setlocal buftype=nofile
  setlocal bufhidden=hide
  setlocal noswapfile
endfunction

function! AIRun(...) range
  let prompt = getline(a:firstline, a:lastline)
  if a:0
    let instruction = join(a:000, ", ") . ":"
    call insert(prompt, instruction, 0)
  endif

  let prompt = join(prompt, "\n")

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
  if !a:0
    echo "Missing edit prompt instruction"
    return
  endif

  let prompt = getline(a:firstline, a:lastline)
  let instruction = join(a:000, ", ") . ":"
  call insert(prompt, instruction, 0)

  let buff_lastline = line('$')
  let prompt = join(prompt, "\n")

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

function! AIChatRun(...)
  let prompt = []
  if search('^>>> user$', 'nw') != 0
    " inside chat window
    let prompt = getline(1, '$')
  else
    " outside chat window
    call ScratchWindow()
    if !a:0
      execute "normal i>>> user\<Enter>\<Enter>"
      return
    endif
    let instruction = join(a:000, ", ")
    call insert(prompt, instruction, 0)
  endif

  let prompt = join(prompt, "\n")

  echo "Answering..."
  let output = system("echo " . shellescape(prompt) . " | python3 " . s:chat_py . " ")

  set paste
  execute "normal! ggdG"
  execute "normal! i" . output . "\<Esc>"
  set nopaste
endfunction

command! -range -nargs=? AI <line1>,<line2>call AIRun(<f-args>)
command! -range -nargs=? AIComplete <line1>,<line2>call AIRun(<f-args>)
command! -range -nargs=? AIEdit <line1>,<line2>call AIEditRun(<f-args>)
command! -range -nargs=? AIChat <line1>,<line2>call AIChatRun(<f-args>)
