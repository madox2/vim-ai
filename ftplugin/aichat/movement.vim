" add markdown pairs and >>> / <<<
setlocal matchpairs-=<:>
let b:match_words = &l:matchpairs .
      \ ',' . '\%(^\|[ (/]\)\@<="' . ':' . '"\ze\%($\|[ )/.\,;\:?!\-]\)' .
      \ ',' . '\%(^\|[ (/]\)\@<=''' . ':' . '''\ze\%($\|[ )/.\,;\:?!\-]\)'
let b:match_words .=
      \ ',' . '\%(^\|[ (/]\)\@<=\*[^*]' . ':' . '[^*]\@<=\*\ze\%($\|[ )/.\,;\:?!\-]\)' .
      \ ',' . '\%(^\|[ (/]\)\@<=\*\*' . ':' . '\*\*\ze\%($\|[ )/.\,;\:?!\-]\)' .
      \ ',' . '\%(^\|[ (/]\)\@<=\*\*\*' . ':' . '\*\*\*\ze\%($\|[ )/.\,;\:?!\-]\)' .
      \ ',' . '\%(^\|[ (/]\)\@<=_[^_]' . ':' . '[^_]\@<=_\ze\%($\|[ )/.\,;\:?!\-]\)' .
      \ ',' . '\%(^\|[ (/]\)\@<=__' . ':' . '__\ze\%($\|[ )/.\,;\:?!\-]\)' .
      \ ',' . '\%(^\|[ (/]\)\@<=___' . ':' . '___\ze\%($\|[ )/.\,;\:?!\-]\)' .
      \ ',' . '\%(^\|[ (/]\)\@<=`[^`]' . ':' . '[^`]\@<=`\ze\%($\|[ )/.\,;\:?!\-]\)' .
      \ ',' . '\%(^\|\s\)\@<=```\w\+$' . ':' . '\%(^\|\s\)\@<=```\ze$' .
      \ ',' . '^>>>\s' . ':' . '^<<<\ze\s'

nnoremap <buffer><silent> ]] :<c-u>call <SID>AIChatJump2Section( v:count1, '' , 0)<CR>
nnoremap <buffer><silent> [[ :<c-u>call <SID>AIChatJump2Section( v:count1, 'b', 0)<CR>
xnoremap <buffer><silent> ]] :<c-u>call <SID>AIChatJump2Section( v:count1, '' , 1)<CR>
xnoremap <buffer><silent> [[ :<c-u>call <SID>AIChatJump2Section( v:count1, 'b', 1)<CR>
onoremap <buffer><silent> ]] :<c-u>normal ]]<CR>
onoremap <buffer><silent> [[ :<c-u>normal [[<CR>

let b:undo_ftplugin .= '|sil! nunmap <buffer> [[|sil! nunmap <buffer> ]]|sil! xunmap <buffer> [[|sil! xunmap <buffer> ]]'

" From https://github.com/plasticboy/vim-markdown/issues/282#issuecomment-725909968
xnoremap <buffer><silent> ic :<C-U>call <SID>AIChatBlockTextObj('i')<CR>
onoremap <buffer><silent> ic :<C-U>call <SID>AIChatBlockTextObj('i')<CR>

xnoremap <buffer><silent> ac :<C-U>call <SID>AIChatBlockTextObj('a')<CR>
onoremap <buffer><silent> ac :<C-U>call <SID>AIChatBlockTextObj('a')<CR>

let b:undo_ftplugin .= '|sil! ounmap <buffer> ic|sil! ounmap <buffer> ac|sil! xunmap <buffer> ic|sil! xunmap <buffer> ac'

" The rest of the file needs to be :sourced only once per session.
if exists('s:loaded_functions') || &cp
  finish
endif
let s:loaded_functions = 1

function! s:AIChatJump2Section( cnt, dir, vis ) abort
  if a:vis
    normal! gv
  endif

  let i = 0
  let pattern = '\v^\>{3,3} user$|^\<{3,3} assistant$'
  let flags = 'W' . a:dir
  while i < a:cnt && search( pattern, flags ) > 0
    let i = i+1
  endwhile
endfunction

function! s:AIChatBlockTextObj(type) abort
  " the parameter type specify whether it is inner text objects or arround
  " text objects.
  let start_row = searchpos('\v^\>{3,3} user$|^\<{3,3} assistant$', 'bn')[0]
  let end_row = searchpos('\v^\>{3,3} user$|^\<{3,3} assistant$', 'n')[0]

  let buf_num = bufnr('%')
  if a:type ==# 'i'
    let start_row += 1
    let end_row -= 1
  endif
  " echo a:type start_row end_row

  call setpos("'<", [buf_num, start_row, 1, 0])
  call setpos("'>", [buf_num, end_row, 1, 0])
  execute 'normal! `<V`>'
endfunction
" See also https://github.com/tpope/vim-markdown/commit/191438f3582a532b72c9f8a1d6c0477050ccddef
nnoremap <buffer><silent> ]] :<c-u>call <SID>AIChatJump2Section( v:count1, '' , 0)<CR>
nnoremap <buffer><silent> [[ :<c-u>call <SID>AIChatJump2Section( v:count1, 'b', 0)<CR>
xnoremap <buffer><silent> ]] :<c-u>call <SID>AIChatJump2Section( v:count1, '' , 1)<CR>
xnoremap <buffer><silent> [[ :<c-u>call <SID>AIChatJump2Section( v:count1, 'b', 1)<CR>
onoremap <buffer><silent> ]] :<c-u>normal ]]<CR>
onoremap <buffer><silent> [[ :<c-u>normal [[<CR>
let b:undo_ftplugin .= '|sil! nunmap <buffer> [[|sil! nunmap <buffer> ]]|sil! xunmap <buffer> [[|sil! xunmap <buffer> ]]'
" From https://github.com/plasticboy/vim-markdown/issues/282#issuecomment-725909968
xnoremap <buffer><silent> ic :<C-U>call <SID>AIChatBlockTextObj('i')<CR>
onoremap <buffer><silent> ic :<C-U>call <SID>AIChatBlockTextObj('i')<CR>

xnoremap <buffer><silent> ac :<C-U>call <SID>AIChatBlockTextObj('a')<CR>
onoremap <buffer><silent> ac :<C-U>call <SID>AIChatBlockTextObj('a')<CR>
let b:undo_ftplugin .= '|sil! ounmap <buffer> ic|sil! ounmap <buffer> ac|sil! xunmap <buffer> ic|sil! xunmap <buffer> ac'
endfunction

function s:AIChatJump2Section( cnt, dir, vis ) abort
if a:vis
  normal! gv
endif

let i = 0
let pattern = '\v^\>{3,3} user$|^\<{3,3} assistant$'
let flags = 'W' . a:dir
while i < a:cnt && search( pattern, flags ) > 0
  let i = i+1
endwhile
endfunction

function s:AIChatBlockTextObj(type) abort
" the parameter type specify whether it is inner text objects or arround
" text objects.
let start_row = searchpos('\v^\>{3,3} user$|^\<{3,3} assistant$', 'bn')[0]
let end_row = searchpos('\v^\>{3,3} user$|^\<{3,3} assistant$', 'n')[0]

let buf_num = bufnr('%')
if a:type ==# 'i'
  let start_row += 1
  let end_row -= 1
endif
" echo a:type start_row end_row

call setpos("'<", [buf_num, start_row, 1, 0])
call setpos("'>", [buf_num, end_row, 1, 0])
execute 'normal! `<V`>'
endfunction
