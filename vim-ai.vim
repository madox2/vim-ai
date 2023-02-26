let g:openaiToken = system("cat ~/.config/openai.token")

function! AIRun() range
  execute a:firstline . ',' . a:lastline . 'd'

  let selection = @*
  call writefile(split(selection, "\n"), "/tmp/vim-ai.temp")

  echo "Working..."
  let output = system("cat /tmp/vim-ai.temp | openai complete - -t " . g:openaiToken)

  call feedkeys("i")
  call feedkeys(output)
  call feedkeys("\<Esc>")
endfunction

command! -range AI <line1>,<line2>call AIRun()
nnoremap <leader>o :call AIRun()<CR>
vnoremap <leader>o :call AIRun()<CR>
