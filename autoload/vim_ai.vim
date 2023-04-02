function! vim_ai#MakeScratchWindow()
  setlocal buftype=nofile
  setlocal bufhidden=hide
  setlocal noswapfile
  setlocal ft=aichat
endfunction
