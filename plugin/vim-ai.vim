" Ensure python3 is available
if !has('python3')
  echoerr "Python 3 support is required for vim-ai plugin"
  finish
endif

" detect if a visual selection is pending
let g:vim_ai_is_selection_pending = 0
augroup vim_ai
  autocmd!
  if exists('##ModeChanged')
    autocmd ModeChanged         *:[vV\x16]*
          \ let g:vim_ai_is_selection_pending = 1
    autocmd ModeChanged [vV\x16]*:*
          \ let g:vim_ai_is_selection_pending =
          \   v:event.new_mode =~# '^c' &&
          \     (getcmdtype() =~# '[/?]' ||
          \      getcmdtype() ==# ':'    && getcmdline() =~# "^\s*'<'>")
  else
    " workaround for version < 8.2.3424 from https://stackoverflow.com/a/20133772
    autocmd CursorMoved *
          \ let g:vim_ai_is_selection_pending = mode() =~# "^[vV\<C-v>]"
    autocmd CmdLineEnter,CmdwinEnter *
          \ if g:vim_ai_is_selection_pending && getcmdtype() ==# ':' |
          \   let g:vim_ai_is_selection_pending = getcmdline() =~# "^\s*'<'>" |
          \ endif
    autocmd CmdLineLeave,CmdwinLeave *
          \ if g:vim_ai_is_selection_pending && getcmdtype() !~# '[/?]' |
          \   let g:vim_ai_is_selection_pending = 0 |
          \ endif
  endif
augroup END

command! -range -nargs=? AI <line1>,<line2>call vim_ai#AIRun(g:vim_ai_is_selection_pending, {}, <f-args>)
command! -range -nargs=? AIEdit <line1>,<line2>call vim_ai#AIEditRun(g:vim_ai_is_selection_pending, {}, <f-args>)
command! -range -nargs=? AIChat <line1>,<line2>call vim_ai#AIChatRun(g:vim_ai_is_selection_pending, {}, <f-args>)
command! -nargs=? AINewChat call vim_ai#AINewChatRun(<f-args>)
command! AIRedo call vim_ai#AIRedoRun()
