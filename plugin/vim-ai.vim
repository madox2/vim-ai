" Ensure python3 is available
if !has('python3')
  echoerr "Python 3 support is required for vim-ai plugin"
  finish
endif

" detect if a visual selection is pending: https://stackoverflow.com/a/20133772
let g:vim_ai_is_selection_pending = 0
augroup vim_ai
  autocmd!
    autocmd CursorMoved *
          \ let g:vim_ai_is_selection_pending = mode() =~# "^[vV\<C-v>]"
augroup END

command! -range   -nargs=? -complete=customlist,vim_ai#RoleCompletion AI        <line1>,<line2>call vim_ai#AIRun({}, <q-args>)
command! -range   -nargs=? -complete=customlist,vim_ai#RoleCompletion AIEdit    <line1>,<line2>call vim_ai#AIEditRun({}, <q-args>)
" Whereas AI and AIEdit default to passing the current line as range
" AIChat defaults to passing nothing which is achieved by -range=0 and passing
" <count> as described at https://stackoverflow.com/a/20133772
command! -range=0 -nargs=? -complete=customlist,vim_ai#RoleCompletion AIChat    <line1>,<line2>call vim_ai#AIChatRun(<count>, {}, <q-args>)
command! -range=0 -nargs=? -complete=customlist,vim_ai#RoleCompletion AINewChat <line1>,<line2>call vim_ai#AINewChatRun(<count>, {}, <q-args>)
command!                                                              AIRedo                   call vim_ai#AIRedoRun()
