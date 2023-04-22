" Ensure python3 is available
if !has('python3')
  echoerr "Python 3 support is required for vim-ai plugin"
  finish
endif

command! -range -nargs=? AI <line1>,<line2>call vim_ai#AIRun(<range>, {}, <f-args>)
command! -range -nargs=? AIEdit <line1>,<line2>call vim_ai#AIEditRun(<range>, {}, <f-args>)
command! -range -nargs=? AIChat <line1>,<line2>call vim_ai#AIChatRun(<range>, {}, <f-args>)
command! AIRedo call vim_ai#AIRedoRun()
