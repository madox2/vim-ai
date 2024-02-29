function! vim_ai_roles#get_roles() abort
  if !filereadable(g:vim_ai_roles_path)
    echoerr 'Error: cannot read file g:vim_ai_roles_path = ' . g:vim_ai_roles_path . '!'
    return
  endif

  let lines = readfile(g:vim_ai_roles_path)
  let roles = {}
  let current_role = ''
  let current_attribute = ''

  for line in lines
    if line =~ '^-\s*name:\s*'
      let current_role = matchstr(line, '^-\s*name:\s*\zs.*')->trim()
      let roles[current_role] = {}
    elseif line =~ '^\s\+\S\+:\s*[^>|]'
      let current_attribute = matchstr(line, '^\s\+\zs[^:[:space:]]\+\ze:\s*[^>|]')->trim()
      let roles[current_role][current_attribute] = matchstr(line, '^\s*' . current_attribute . ':\zs.*')->trim()
    elseif line =~ '^\s\+\S\+:\s*[>|]'
      let current_attribute = matchstr(line, '^\s\+\zs\S\+\ze:\s*[>|]')->trim()
      let roles[current_role][current_attribute] = ''
    else
      let roles[current_role][current_attribute] .= line->trim() . "\n"
    endif
  endfor

  return roles
endfunction

function! vim_ai_roles#completion(A,L,P) abort
  if !filereadable(g:vim_ai_roles_path)
    echoerr 'Error: cannot read file g:vim_ai_roles_path = ' . g:vim_ai_roles_path . '!'
    return ''
  endif
  let roles = keys(vim_ai_roles#get_roles())
  call map(roles, "'/' . v:val")
  return filter(roles, 'v:val =~ "^' . a:A . '"')
endfunction

function! vim_ai_roles#set_config_role(config, role) abort
  let roles = vim_ai_roles#get_roles()
  try
    if !has_key(roles, a:role)
      throw "The role " . a:role . " does not exist!"
    endif
    if !has_key(roles[a:role], 'prompt')
      throw "The role " . a:role . " does not have a prompt!"
    endif
  endtry
  let a:config.options.initial_prompt =
        \ ">>> system\n" . roles[a:role].prompt
  if has_key(roles[a:role], 'temperature')
    let a:config.temperature = roles[a:role].temperature
  endif
endfunction
