if !(has("folding") && get(g:,'vim_ai_folding', 0) | finish | endif

" Similar to https://github.com/tpope/vim-markdown/issues/154
" setlocal foldexpr=AIChatFold() foldmethod=expr foldtext=AIChatFoldText()
augroup AichatFold
  autocmd! * <buffer>
  autocmd vim_ai BufWinEnter <buffer>  setlocal foldexpr=AIChatFold() foldmethod=expr foldtext=AIChatFoldText()
augroup END

if exists('b:undo_ftplugin')
  let b:undo_ftplugin .= "|setl foldexpr< foldmethod< foldtext<"
else
  let b:undo_ftplugin  = "|setl foldexpr< foldmethod< foldtext<"
endif

if exists('s:loaded_functions') || &cp
  finish
endif
let s:loaded_functions = 1

function! AIChatFold() abort
  return getline(v:lnum) =~# '^>>> user$' ? '>1' : '='
endfunction

function! AIChatFoldText() abort
  "get first non-blank line
  let fs = nextnonblank(v:foldstart + 1)
  if fs > v:foldend
    let head = getline(v:foldstart)
  else
    let head = substitute(getline(fs), '\t', repeat(' ', &tabstop), 'g')
  endif
  unlet fs

  let foldsize = (v:foldend - v:foldstart + 1)
  let digits = len(string(line('$')))
  let foldsize = printf("%" . digits . "s", foldsize)
  let tail = '[' . foldsize . ' lines]'

  " " truncate foldtext according to window width
  let maxWidth = winwidth(0) - &foldcolumn - (&number ? &numberwidth : 0) - (&signcolumn is# 'yes' ? 2 : 0)
  let maxLengthHead = maxWidth - strwidth(tail)
  if strwidth(head) > maxLengthHead
    let cutLengthHead = maxLengthHead - strwidth('..')
    if cutLengthHead < 0
      let cutLengthHead = 0
    endif
    let head = strpart(head, 0, cutLengthHead) . '..'
  endif

  let middle = repeat(' ', maxWidth - strwidth(head . tail))

  return head . middle . tail
endfunction
