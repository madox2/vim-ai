let g:vim_ai_providers = {}

function! vim_ai_provider#Register(name, options)
  let g:vim_ai_providers[a:name] = a:options
endfunction
