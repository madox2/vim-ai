let g:openaiToken = system("cat ~/.config/openai.token")

function! AIRun(...) range
  let selection = getline(a:firstline, a:lastline)
  if a:0
    let instruction = a:1 . ":"
    call insert(selection, instruction, 0)
  endif

  let buff_lastline = line('$')

  call writefile(selection, "/tmp/vim-ai.temp")

  echo "Completing..."
  let output = system("cat /tmp/vim-ai.temp | openai complete - -t " . g:openaiToken)
  let output = trim(output)

  execute a:firstline . ',' . a:lastline . 'd'

  if a:lastline == buff_lastline
    execute "normal! o" . output . "\<Esc>"
  else
    execute "normal! O" . output . "\<Esc>"
  endif

endfunction

command! -range -nargs=? AI <line1>,<line2>call AIRun(<f-args>)
nnoremap <leader>o :call AIRun()<CR>
vnoremap <leader>o :call AIRun()<CR>
