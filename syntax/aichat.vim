if exists("b:current_syntax")
  finish
endif

if get(g:, 'aichat_markdown', 0) == 1
  runtime! syntax/markdown.vim
endif

syntax match aichatRole ">>> system"
syntax match aichatRole ">>> user"
syntax match aichatRole ">>> include"
syntax match aichatRole "<<< assistant"

highlight default link aichatRole Comment

syntax region userInput start=/^>>>\s\+/hs=e end=/^\ze<<<\s\+/ keepend contains=aichatRole
highlight link userInput NONE

let b:current_syntax = 'aichat'
