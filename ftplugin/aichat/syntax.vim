" Highlighting code blocks in .aichat files
" Inspired and based on https://github.com/preservim/vim-markdown

if exists('g:vim_markdown_fenced_languages')
  let s:filetype_dict = {}
  for s:filetype in g:vim_markdown_fenced_languages
    let key = matchstr(s:filetype, '[^=]*')
    let val = matchstr(s:filetype, '[^=]*$')
    let s:filetype_dict[key] = val
  endfor
else
  let s:filetype_dict = {
        \ 'c++': 'cpp',
        \ 'viml': 'vim',
        \ 'bash': 'sh',
        \ 'ini': 'dosini',
        \ 'js': 'javascript',
        \ 'jsx': 'javascriptreact',
        \ 'ts': 'typescript',
        \ 'tsx': 'typescriptreact',
        \ }
endif

function! s:MarkdownHighlightSources(force)
  " Syntax highlight source code embedded in notes.
  " Look for code blocks in the current file
  let filetypes = {}
  for line in getline(1, '$')
    let ft = matchstr(line, '\(`\{3,}\|\~\{3,}\)\s*\zs[0-9A-Za-z_+-]*\ze.*')
    if !empty(ft) && ft !~# '^\d*$' | let filetypes[ft] = 1 | endif
  endfor
  if !exists('b:aichat_known_filetypes')
    let b:aichat_known_filetypes = {}
  endif
  if !exists('b:aichat_included_filetypes')
    " set syntax file name included
    let b:aichat_included_filetypes = {}
  endif
  if !a:force && (b:aichat_known_filetypes == filetypes || empty(filetypes))
    return
  endif

  " Now we're ready to actually highlight the code blocks.
  let startgroup = 'aichatCodeStart'
  let endgroup = 'aichatCodeEnd'
  for ft in keys(filetypes)
    if a:force || !has_key(b:aichat_known_filetypes, ft)
      if has_key(s:filetype_dict, ft)
        let filetype = s:filetype_dict[ft]
      else
        let filetype = ft
      endif
      let group = 'aichatSnippet' . toupper(substitute(filetype, '[+-]', '_', 'g'))
      if !has_key(b:aichat_included_filetypes, filetype)
        let include = s:SyntaxInclude(filetype)
        let b:aichat_included_filetypes[filetype] = 1
      else
        let include = '@' . toupper(filetype)
      endif
      let command_backtick = 'syntax region %s matchgroup=%s start="^\s*`\{3,}\s*%s.*$" matchgroup=%s end="\s*`\{3,}\s*$" keepend contains=%s'
      let command_tilde    = 'syntax region %s matchgroup=%s start="^\s*\~\{3,}\s*%s.*$" matchgroup=%s end="\s*\~\{3,}\s*$" keepend contains=%s'
      execute printf(command_backtick, group, startgroup, ft, endgroup, include)
      execute printf(command_tilde,    group, startgroup, ft, endgroup, include)
      execute printf('syntax cluster aichatNonListItem add=%s', group)

      let b:aichat_known_filetypes[ft] = 1
    endif
  endfor
endfunction

function! s:MarkdownHighlightChatOptions(force)
  " use jproperties syntax to highlight chat options
  let filetype = 'jproperties'
  if a:force || !has_key(b:aichat_known_filetypes, filetype)
    if !has_key(b:aichat_included_filetypes, filetype)
      let include = s:SyntaxInclude(filetype)
      let b:aichat_included_filetypes[filetype] = 1
    else
      let include = '@' . toupper(filetype)
    endif
    syntax region aichatOptions start="\[chat-options\]" end="^$" contains=@JPROPERTIES
    let b:aichat_known_filetypes[filetype] = 1
  endif
endfunction

function! s:SyntaxInclude(filetype)
  " Include the syntax highlighting of another {filetype}.
  let grouplistname = '@' . toupper(a:filetype)
  " Unset the name of the current syntax while including the other syntax
  " because some syntax scripts do nothing when "b:current_syntax" is set
  if exists('b:current_syntax')
    let syntax_save = b:current_syntax
    unlet b:current_syntax
  endif
  try
    execute 'syntax include' grouplistname 'syntax/' . a:filetype . '.vim'
    execute 'syntax include' grouplistname 'after/syntax/' . a:filetype . '.vim'
  catch /E484/
    " Ignore missing scripts
  endtry
  " Restore the name of the current syntax
  if exists('syntax_save')
    let b:current_syntax = syntax_save
  elseif exists('b:current_syntax')
    unlet b:current_syntax
  endif
  return grouplistname
endfunction

function! s:IsHighlightSourcesEnabledForBuffer()
  " Enable for markdown buffers, and for liquid buffers with markdown format
  return &filetype =~# 'aichat' || get(b:, 'liquid_subtype', '') =~# 'aichat'
endfunction

function! s:MarkdownRefreshSyntax(force)
  call vim_ai_config#load()
  if g:vim_ai_chat_default['ui']['code_syntax_enabled'] && &filetype =~# 'aichat'
    call s:MarkdownHighlightSources(a:force)
    call s:MarkdownHighlightChatOptions(a:force)
  endif

endfunction

function! s:MarkdownClearSyntaxVariables()
  if exists('b:aichat_included_filetypes')
    unlet! b:aichat_included_filetypes
  endif
endfunction

augroup AichatSyntax
  autocmd! * <buffer>
  autocmd BufWinEnter <buffer> call s:MarkdownRefreshSyntax(1)
  autocmd BufUnload <buffer> call s:MarkdownClearSyntaxVariables()
  autocmd BufWritePost <buffer> call s:MarkdownRefreshSyntax(0)
  autocmd InsertEnter,InsertLeave <buffer> call s:MarkdownRefreshSyntax(0)
  autocmd CursorHold,CursorHoldI <buffer> call s:MarkdownRefreshSyntax(0)
augroup END
