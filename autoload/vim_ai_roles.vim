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
  return filter(keys(vim_ai_roles#get_roles()), 'v:val =~ "^' . a:A . '"')
endfunction

function! vim_ai_roles#get_config(role) abort
  let roles = vim_ai_roles#get_roles()
  if !has_key(roles, a:role)
    echoerr "Specified role does not exist!"
    return
  endif
  if !has_key(roles[a:role], 'prompt')
    echoerr "Specified role does not have a prompt!"
    return
  endif
  let config = { "options": { "initial_prompt":
        \ ">>> system\n" . roles[a:role].prompt, },}
  if has_key(roles[a:role], 'temperature')
    let config.temperature = roles[a:role].temperature
  endif

  return config
endfunction

function! vim_ai_roles#AIRunAs(qargs) range abort
  let i = match(trim(a:qargs) . ' ', '\s')
  let role = a:qargs[0:i-1]
  let l:prompt = a:qargs[i:-1]
  let l:config = vim_ai_roles#get_config(role)
  exe a:firstline.",".a:lastline . "call vim_ai#AIRun(l:config, l:prompt)"
endfunction

function! vim_ai_roles#AIEditRunAs(qargs) range abort
  let i = match(trim(a:qargs) . ' ', '\s')
  let role = a:qargs[0:i-1]
  let l:prompt = a:qargs[i:-1]
  let l:config = vim_ai_roles#get_config(role)
  exe a:firstline.",".a:lastline . "call vim_ai#AIEditRun(l:config, l:prompt)"
endfunction

function! vim_ai_roles#AIChatRunAs(uses_range, qargs) range abort
  let i = match(trim(a:qargs) . ' ', '\s')
  let role = a:qargs[0:i-1]
  let l:prompt = a:qargs[i:-1]
  let l:config = vim_ai_roles#get_config(role)
  exe a:firstline.",".a:lastline . "call vim_ai#AIChatRun(a:uses_range, l:config, l:prompt)"
endfunction
