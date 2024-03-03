function! vim_ai_roles#get_roles() abort
  if isdirectory(g:vim_ai_roles_path)
    return vim_ai_roles#get_roles_folder(g:vim_ai_roles_path)
  elseif filereadable(g:vim_ai_roles_path)
    return vim_ai_roles#get_roles_file(g:vim_ai_roles_path)
  else
    throw 'g:vim_ai_roles_path = ' . g:vim_ai_roles_path . ' must be a valid path'
  endif
endfunction

function! vim_ai_roles#get_roles_folder(folder) abort
  if !isdirectory(a:folder)
    throw 'cannot read folder ' . a:folder
  endif

  let file_dictionary = {}
  for file in split(glob(a:folder . '/*.aichat'), '\n')
    let file_name = fnamemodify(file, ':t:r')
    let file_dictionary[file_name] = s:ParseChatHeaderOptions(file)
  endfor
  return file_dictionary
endfunction

function! s:ParseChatHeaderOptions(filepath)
  let lines = readfile(a:filepath)
  try
    let options = {}
    let contains_chat_options = index(lines, '[chat-options]') != -1
    if contains_chat_options
      let options_index = index(lines, '[chat-options]')
      let i = options_index + 1
      while i < len(lines)
        let line = lines[i]
        if line =~ '^\s*#'
          " Ignore comments
          let i += 1
          continue
        endif
        if line == ''
          " Stop at the end of the region
          break
        endif
        let parts = split(line, '=')
        if len(parts) == 2
          let key = parts[0]
          let value = parts[1]
          if key == 'initial_prompt'
            let value = split(value, '\\n')
          endif
          let options[key] = value
        endif
        let i += 1
      endwhile
    endif
    return options
  catch
    throw "Invalid [chat-options] in file " . a:filepath
  endtry
endfunction

function! vim_ai_roles#get_roles_file(file) abort
  if !filereadable(a:file)
    throw 'cannot read file ' . a:file
  endif

  let lines = readfile(a:file)
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

  " convert to vim-ai config dictionary form
  for role in keys(roles)
    let roles[role].options = {}
    if has_key(roles[role], 'prompt')
      let roles[role].options.initial_prompt = ">>> system\n" . roles[role].prompt
      unlet roles[role].prompt
    endif
    if has_key(roles[role], 'temperature')
      let roles[role].options.temperature = roles[role].temperature
      unlet roles[role].temperature
    endif
  endfor
  return roles
endfunction

function! vim_ai_roles#completion(A,L,P) abort
  let roles = keys(vim_ai_roles#get_roles())
  call map(roles, '"/" . v:val')
  return filter(roles, 'v:val =~ "^' . a:A . '"')
endfunction

function! vim_ai_roles#set_config_role(config, role) abort
  let roles = vim_ai_roles#get_roles()
  try
    if !has_key(roles, a:role)
      throw "The role " . a:role . " does not exist!"
    endif
    if !has_key(roles[a:role].options, 'initial_prompt')
      throw "The role " . a:role . " does not have a prompt!"
    endif
  catch
    echohl ErrorMsg | echomsg v:exception | echohl None
  endtry
  return vim_ai_config#ExtendDeep(deepcopy(a:config), roles[a:role])
endfunction
