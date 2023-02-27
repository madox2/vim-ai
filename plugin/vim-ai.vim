let g:openaiToken = system("cat ~/.config/openai.token")

function! AIRun(...) range
  let prompt = getline(a:firstline, a:lastline)
  if a:0
    " join arguments and prepend to the prompt
    let instruction = join(a:000, ", ") . ":"
    call insert(prompt, instruction, 0)
  endif

  let buff_lastline = line('$')
  let prompt = join(prompt, "\n")

  echo "Completing..."
  let output = system("echo " . shellescape(prompt) . " | openai complete - -t " . g:openaiToken)
  let output = trim(output)

  execute a:firstline . ',' . a:lastline . 'd'

  if a:lastline == buff_lastline
    execute "normal! o" . output . "\<Esc>"
  else
    execute "normal! O" . output . "\<Esc>"
  endif

endfunction

command! -range -nargs=? AI <line1>,<line2>call AIRun(<f-args>)
