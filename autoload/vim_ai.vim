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
