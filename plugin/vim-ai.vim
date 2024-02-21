" Ensure python3 is available
if !has('python3')
  echoerr "Python 3 support is required for vim-ai plugin"
  finish
endif

" to detect if a selection pending: https://stackoverflow.com/a/20133772
augroup vim_ai
  autocmd!
  autocmd CursorMoved * let g:vim_ai_is_selection_pending = mode() =~# "^[vV\<C-v>]"
augroup END

command! -range -nargs=? AI <line1>,<line2>call vim_ai#AIRun(g:vim_ai_is_selection_pending, {}, <f-args>)
command! -range -nargs=? AIEdit <line1>,<line2>call vim_ai#AIEditRun(g:vim_ai_is_selection_pending, {}, <f-args>)
command! -range -nargs=? AIChat <line1>,<line2>call vim_ai#AIChatRun(g:vim_ai_is_selection_pending, {}, <f-args>)
command! -nargs=? AINewChat call vim_ai#AINewChatRun(<f-args>)
command! AIRedo call vim_ai#AIRedoRun()
