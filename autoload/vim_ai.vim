call vim_ai_config#load()

let s:plugin_root = expand('<sfile>:p:h:h')

" remembers last command parameters to be used in AIRedoRun
let s:last_is_selection = 0
let s:last_firstline = 1
let s:last_lastline = 1
let s:last_instruction = ""
let s:last_command = ""
let s:last_config = {}

let s:scratch_buffer_name = ">>> AI chat"

function! s:ImportPythonModules()
  for py_module in ['types', 'utils', 'context', 'chat', 'complete', 'roles', 'image']
    if !py3eval("'" . py_module . "_py_imported' in globals()")
      execute "py3file " . s:plugin_root . "/py/" . py_module . ".py"
    endif
  endfor
endfunction

function! s:StartsWith(longer, shorter) abort
  return a:longer[0:len(a:shorter)-1] ==# a:shorter
endfunction

function! s:GetLastScratchBufferName()
  let l:all_buffer_names = map(map(filter(copy(getbufinfo()), 'v:val.listed'), 'v:val.bufnr'), 'bufname(v:val)')
  let l:buffer_name = -1
  for l:name in l:all_buffer_names
    if s:StartsWith(l:name, s:scratch_buffer_name)
      let l:buffer_name = l:name
    endif
  endfor
  return l:buffer_name
endfunction

" Configures ai-chat scratch window.
" - scratch_buffer_keep_open = 0
"   - opens new ai-chat every time
"   - excludes buffer from buffer list
" - scratch_buffer_keep_open = 1
"   - opens last ai-chat buffer (unless force_new = 1)
"   - keeps the buffer in the buffer list
function! s:OpenChatWindow(open_conf, force_new) abort
  " open new buffer that will be used as a chat
  let l:open_cmd = has_key(g:vim_ai_open_chat_presets, a:open_conf)
        \ ? g:vim_ai_open_chat_presets[a:open_conf]
        \ : a:open_conf
  execute l:open_cmd

  " reuse chat in keep-open mode
  let l:keep_open = g:vim_ai_chat['ui']['scratch_buffer_keep_open'] == '1'
  let l:last_scratch_buffer_name = s:GetLastScratchBufferName()
  if l:keep_open && bufexists(l:last_scratch_buffer_name) && !a:force_new
    let l:current_buffer = bufnr('%')
    " reuse chat buffer
    execute "buffer " . l:last_scratch_buffer_name
    " close new buffer that was created by l:open_cmd
    execute "bd " . l:current_buffer
    return
  endif

  setlocal buftype=nofile
  setlocal noswapfile
  setlocal ft=aichat
  if l:keep_open
    setlocal bufhidden=hide
  else
    setlocal bufhidden=wipe
  endif
  if bufexists(s:scratch_buffer_name)
    " spawn another window if chat already exist
    let l:index = 2
    while bufexists(s:scratch_buffer_name . " " . l:index)
      let l:index += 1
    endwhile
    execute "file " . s:scratch_buffer_name . " " . l:index
  else
    execute "file " . s:scratch_buffer_name
  endif
endfunction

let s:is_handling_paste_mode = 0

function! s:set_paste(config)
  if !&paste && a:config['ui']['paste_mode'] == '1'
    let s:is_handling_paste_mode = 1
    setlocal paste
  endif
endfunction

function! s:set_nopaste(config)
  if s:is_handling_paste_mode
    setlocal nopaste
    let s:is_handling_paste_mode = 0
  endif
endfunction

function! s:GetSelectionOrRange(is_selection, is_range, ...)
  if a:is_selection
    return s:GetVisualSelection()
  elseif a:is_range
    return trim(join(getline(a:1, a:2), "\n"))
  else
    return ""
  endif
endfunction

function! s:SelectSelectionOrRange(is_selection, ...)
  if a:is_selection
    execute "normal! gv"
  else
    execute 'normal!' . a:1 . 'GV' . a:2 . 'G'
  endif
endfunction

function! s:GetVisualSelection()
  let [line_start, column_start] = getpos("'<")[1:2]
  let [line_end, column_end] = getpos("'>")[1:2]
  let lines = getline(line_start, line_end)
  if len(lines) == 0
    return ''
  endif
  " The exclusive mode means that the last character of the selection area is not included in the operation scope.
  let lines[-1] = lines[-1][: column_end - (&selection == 'inclusive' ? 1 : 2)]
  let lines[0] = lines[0][column_start - 1:]
  return join(lines, "\n")
endfunction

" Complete prompt
" - uses_range   - truty if range passed
" - config       - function scoped vim_ai_complete config
" - a:1          - optional instruction prompt
function! vim_ai#AIRun(uses_range, config, ...) range abort
  call s:ImportPythonModules()
  let l:instruction = a:0 > 0 ? a:1 : ""
  let l:is_selection = a:uses_range && a:firstline == line("'<") && a:lastline == line("'>")
  let l:selection = s:GetSelectionOrRange(l:is_selection, a:uses_range, a:firstline, a:lastline)

  let l:config_input = {
  \  "config_default": g:vim_ai_complete,
  \  "config_extension": a:config,
  \  "user_instruction": l:instruction,
  \  "user_selection": l:selection,
  \  "is_selection": l:is_selection,
  \  "command_type": 'complete',
  \}
  let l:context = py3eval("make_ai_context(unwrap('l:config_input'))")
  let l:config = l:context['config']

  let s:last_command = "complete"
  let s:last_config = a:config
  let s:last_instruction = l:instruction
  let s:last_is_selection = l:is_selection
  let s:last_firstline = a:firstline
  let s:last_lastline = a:lastline

  let l:cursor_on_empty_line = empty(getline('.'))
  try
    call s:set_paste(l:config)
    if l:cursor_on_empty_line
      execute "normal! " . a:lastline . "GA"
    else
      execute "normal! " . a:lastline . "Go"
    endif
    py3 run_ai_completition(unwrap('l:context'))
    execute "normal! " . a:lastline . "G"
  finally
    call s:set_nopaste(l:config)
  endtry
endfunction

" Edit prompt
" - uses_range   - truty if range passed
" - config       - function scoped vim_ai_edit config
" - a:1          - optional instruction prompt
function! vim_ai#AIEditRun(uses_range, config, ...) range abort
  call s:ImportPythonModules()
  let l:instruction = a:0 > 0 ? a:1 : ""
  let l:is_selection = a:uses_range && a:firstline == line("'<") && a:lastline == line("'>")
  let l:selection = s:GetSelectionOrRange(l:is_selection, a:uses_range, a:firstline, a:lastline)

  let l:config_input = {
  \  "config_default": g:vim_ai_edit,
  \  "config_extension": a:config,
  \  "user_instruction": l:instruction,
  \  "user_selection": l:selection,
  \  "is_selection": l:is_selection,
  \  "command_type": 'edit',
  \}
  let l:context = py3eval("make_ai_context(unwrap('l:config_input'))")
  let l:config = l:context['config']

  let s:last_command = "edit"
  let s:last_config = a:config
  let s:last_instruction = l:instruction
  let s:last_is_selection = l:is_selection
  let s:last_firstline = a:firstline
  let s:last_lastline = a:lastline

  try
    call s:set_paste(l:config)
    call s:SelectSelectionOrRange(l:is_selection, a:firstline, a:lastline)
    execute "normal! c"
    py3 run_ai_completition(unwrap('l:context'))
  finally
    call s:set_nopaste(l:config)
  endtry
endfunction

" Generate image
" - uses_range   - truty if range passed
" - config       - function scoped vim_ai_image config
" - a:1          - optional instruction prompt
function! vim_ai#AIImageRun(uses_range, config, ...) range abort
  call s:ImportPythonModules()
  let l:instruction = a:0 > 0 ? a:1 : ""
  let l:is_selection = a:uses_range && a:firstline == line("'<") && a:lastline == line("'>")
  let l:selection = s:GetSelectionOrRange(l:is_selection, a:uses_range, a:firstline, a:lastline)

  let l:config_input = {
  \  "config_default": g:vim_ai_image,
  \  "config_extension": a:config,
  \  "user_instruction": l:instruction,
  \  "user_selection": l:selection,
  \  "is_selection": l:is_selection,
  \  "command_type": 'image',
  \}
  let l:context = py3eval("make_ai_context(unwrap('l:config_input'))")
  let l:config = l:context['config']

  let s:last_command = "image"
  let s:last_config = a:config
  let s:last_instruction = l:instruction
  let s:last_is_selection = l:is_selection
  let s:last_firstline = a:firstline
  let s:last_lastline = a:lastline

  py3 run_ai_image(unwrap('l:context'))
endfunction

function! s:ReuseOrCreateChatWindow(config)
  let l:open_conf = a:config['ui']['open_chat_command']

  if a:config['ui']['force_new_chat'] == '1'
    call s:OpenChatWindow(l:open_conf, 1)
    return
  endif

  if &filetype != 'aichat'
    " reuse chat in active window or tab
    let l:chat_win_ids = win_findbuf(bufnr(s:scratch_buffer_name))
    if !empty(l:chat_win_ids)
      call win_gotoid(l:chat_win_ids[0])
      return
    endif

    " reuse .aichat file on the same tab
    let buffer_list_tab = tabpagebuflist(tabpagenr())
    let buffer_list_tab = filter(buffer_list_tab, 'getbufvar(v:val, "&filetype") ==# "aichat"')
    if len(buffer_list_tab) > 0
      call win_gotoid(win_findbuf(buffer_list_tab[0])[0])
      return
    endif

    " reuse any .aichat buffer in the session
    let buffer_list = []
    for i in range(tabpagenr('$'))
      call extend(buffer_list, tabpagebuflist(i + 1))
    endfor
    let buffer_list = filter(buffer_list, 'getbufvar(v:val, "&filetype") ==# "aichat"')
    if len(buffer_list) > 0
      call win_gotoid(win_findbuf(buffer_list[0])[0])
      return
    endif

    " open new chat window if no active buffer found
    call s:OpenChatWindow(l:open_conf, 0)
  endif
endfunction

" Start and answer the chat
" - uses_range   - truty if range passed
" - config       - function scoped vim_ai_chat config
" - a:1          - optional instruction prompt
function! vim_ai#AIChatRun(uses_range, config, ...) range abort
  call s:ImportPythonModules()
  let l:instruction = a:0 > 0 ? a:1 : ""
  let l:is_selection = a:uses_range && a:firstline == line("'<") && a:lastline == line("'>")
  let l:selection = s:GetSelectionOrRange(l:is_selection, a:uses_range, a:firstline, a:lastline)
  let l:started_from_chat = &filetype == 'aichat'

  let l:config_input = {
  \  "config_default": g:vim_ai_chat,
  \  "config_extension": a:config,
  \  "user_instruction": l:instruction,
  \  "user_selection": l:selection,
  \  "is_selection": l:is_selection,
  \  "command_type": 'chat',
  \}
  let l:context = py3eval("make_ai_context(unwrap('l:config_input'))")
  let l:config = l:context['config']
  let l:context['prompt'] = a:0 > 0 || a:uses_range ? l:context['prompt'] : ''
  let l:context['started_from_chat'] = l:started_from_chat
  let l:context['bufnr'] = bufnr()
  let l:bufnr = bufnr()

  if py3eval("ai_job_pool.isjobdone(unwrap('l:bufnr'))") == 0
    echoerr "Operation in progress, wait or stop it with :AIStopChat"
    return
  endif

  try
    call s:set_paste(l:config)
    call s:ReuseOrCreateChatWindow(l:config)

    let s:last_command = "chat"
    let s:last_config = a:config

    py3 run_ai_chat(unwrap('l:context'))
    call appendbufline(l:bufnr, '$', "<<< thinking .")
    call timer_start(1000, function('vim_ai#AIChatWatch', [l:bufnr, 0]))
  finally
    call s:set_nopaste(l:config)
  endtry
endfunction

" Cancel current chat job
function! vim_ai#AIChatStopRun() abort
  if &filetype !=# 'aichat'
    echoerr "Not in an AI chat buffer."
    return
  endif
  let l:bufnr = bufnr('%')
  call s:ImportPythonModules() " Ensure chat.py is loaded
  py3 ai_job_pool.cancel_job(unwrap('l:bufnr'))
endfunction


function! vim_ai#AIChatWatch(bufnr, anim, timerid) abort
  " inject new lines, first check if it is done to avoid data race, we do not
  " mind if we run the timer one more time, but we want all the data
  let l:done = py3eval("ai_job_pool.isjobdone(unwrap('a:bufnr'))")
  let l:result = py3eval("ai_job_pool.pickuplines(unwrap('a:bufnr'))")
  call deletebufline(a:bufnr, '$')
  call appendbufline(a:bufnr, '$', l:result)

  " if not done, queue timer
  if l:done == 0
    if a:anim == 0
      call timer_start(1000, function('vim_ai#AIChatWatch', [a:bufnr, 1]))
      call appendbufline(a:bufnr, '$', "<<< thinking ..")
    else
      call timer_start(1000, function('vim_ai#AIChatWatch', [a:bufnr, 0]))
      call appendbufline(a:bufnr, '$', "<<< thinking ...")
    endif
  else
    call appendbufline(a:bufnr, '$', ["", ">>> user", "", ""])
    " Clear message
    " https://neovim.discourse.group/t/how-to-clear-the-echo-message-in-the-command-line/268/3
    call feedkeys(':','nx')
  end

  " if window is visible, scroll down
  let winid = bufwinid(a:bufnr)
  if winid != -1
    call win_execute(winid, "normal! G")
  endif
endfunction

" Start a new chat
" a:1 - optional preset shorcut (below, right, tab)
function! vim_ai#AINewChatDeprecatedRun(...)
  echoerr ":AINew is deprecated, use pre-configured roles `/tab`, `/below`, `/right` instead (e.g. `:AIChat /right`)"
endfunction

" Repeat last AI command
function! vim_ai#AIRedoRun() abort
  if s:last_command !=# "image"
    undo
  endif
  if s:last_command ==# "complete"
    exe s:last_firstline.",".s:last_lastline . "call vim_ai#AIRun(s:last_is_selection, s:last_config, s:last_instruction)"
  elseif s:last_command ==# "edit"
    exe s:last_firstline.",".s:last_lastline . "call vim_ai#AIEditRun(s:last_is_selection, s:last_config, s:last_instruction)"
  elseif s:last_command ==# "image"
    exe s:last_firstline.",".s:last_lastline . "call vim_ai#AIImageRun(s:last_is_selection, s:last_config, s:last_instruction)"
  elseif s:last_command ==# "chat"
    " chat does not need prompt, all information are in the buffer already
    call vim_ai#AIChatRun(0, s:last_config)
  endif
endfunction

function! s:RoleCompletion(A, command_type) abort
  if a:A !~# '^/' | return [] | endif
  call s:ImportPythonModules()
  let l:role_list = py3eval("load_ai_role_names(unwrap('a:command_type'))")
  call map(l:role_list, '"/" . v:val')
  return filter(l:role_list, 'v:val =~ "^' . a:A . '"')
endfunction

function! vim_ai#RoleCompletionComplete(A,L,P) abort
  return s:RoleCompletion(a:A, 'complete')
endfunction

function! vim_ai#RoleCompletionImage(A,L,P) abort
  return s:RoleCompletion(a:A, 'image')
endfunction

function! vim_ai#RoleCompletionEdit(A,L,P) abort
  return s:RoleCompletion(a:A, 'edit')
endfunction

function! vim_ai#RoleCompletionChat(A,L,P) abort
  return s:RoleCompletion(a:A, 'chat')
endfunction

function! vim_ai#AIUtilRolesOpen() abort
  execute "e " . g:vim_ai_roles_config_file
endfunction

function! vim_ai#AIUtilSetDebug(is_debug) abort
  let g:vim_ai_debug = a:is_debug
endfunction
