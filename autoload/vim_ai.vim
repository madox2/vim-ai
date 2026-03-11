call vim_ai_config#load()

let s:plugin_root = expand('<sfile>:p:h:h')

" remembers last command parameters to be used in AIRedoRun
let s:last_is_selection = 0
let s:last_uses_range = 0
let s:last_firstline = 1
let s:last_lastline = 1
let s:last_instruction = ""
let s:last_command = ""
let s:last_config = {}
let s:redo_selection_hint = -1
let s:redo_firstline = 1
let s:redo_lastline = 1

let s:scratch_buffer_name = ">>> AI chat"
let s:chat_redraw_interval = 250 " milliseconds

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

function! s:GetLastChatBufferNumber()
  let l:chat_buffers = []
  for l:buf in reverse(getbufinfo())
    let l:bufname = bufname(l:buf.bufnr)
    if l:buf.listed && s:StartsWith(l:bufname, s:scratch_buffer_name)
      return l:buf.bufnr
    endif
  endfor
  return -1
endfunction

function! s:GetTabLocalChatBufferNumber()
  let l:chat_bufnr = gettabvar(tabpagenr(), 'vim_ai_chat_bufnr', -1)
  if !bufexists(l:chat_bufnr) || !buflisted(l:chat_bufnr)
    return -1
  endif
  return l:chat_bufnr
endfunction

function! s:GetReusedChatBufferNumber()
  " reuse tab local buffer if available
  let l:tab_local_buffnr = s:GetTabLocalChatBufferNumber()
  if l:tab_local_buffnr != -1
    return l:tab_local_buffnr
  endif
  " else reuse last chat buffer
  let l:last_scratch_buffnum = s:GetLastChatBufferNumber()
  return l:last_scratch_buffnum
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
  let l:reused_chat_buffer_name = s:GetReusedChatBufferNumber()
  if l:keep_open && l:reused_chat_buffer_name != -1 && !a:force_new
    let l:current_buffer = bufnr('%')
    " reuse chat buffer
    execute "buffer " . l:reused_chat_buffer_name
    " close new buffer that was created by l:open_cmd
    if bufloaded(l:current_buffer)
        " if `hidden` is turned off, the buffer is unloaded automatically
        execute "bd " . l:current_buffer
    endif
    " set tab local chat buffer number
    call settabvar(tabpagenr(), 'vim_ai_chat_bufnr', bufnr('%'))
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
  " set tab local chat buffer number
  call settabvar(tabpagenr(), 'vim_ai_chat_bufnr', bufnr('%'))
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
    execute a:1
    execute "normal! V"
    execute a:2
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

" A visual range should be treated as character-wise selection only when
" command-line invocation actually came from `'<,'>...`.
function! s:IsVisualSelectionRange(uses_range, line_start, line_end, ...) abort
  if !a:uses_range
    return 0
  endif

  if s:redo_selection_hint >= 0
    return s:redo_selection_hint
      \ && a:line_start == line("'<")
      \ && a:line_end == line("'>")
  endif

  let l:last_cmd = a:0 > 0 ? a:1 : histget(':', -1)
  if l:last_cmd =~# '^\s*AIRedo\>'
    return a:line_start == line("'<") && a:line_end == line("'>")
  endif

  return l:last_cmd =~# '^\s*''<,''>' && a:line_start == line("'<") && a:line_end == line("'>")
endfunction

function! vim_ai#IsVisualSelectionRange(uses_range, line_start, line_end, ...) abort
  return call(function('s:IsVisualSelectionRange'), [a:uses_range, a:line_start, a:line_end] + a:000)
endfunction

" Complete prompt
" - uses_range   - truty if range passed
" - config       - function scoped vim_ai_complete config
" - a:1          - optional instruction prompt
function! vim_ai#AIRun(uses_range, config, ...) range abort
  call s:ImportPythonModules()
  let l:instruction = a:0 > 0 ? a:1 : ""
  let l:firstline = s:redo_selection_hint >= 0 ? s:redo_firstline : a:firstline
  let l:lastline = s:redo_selection_hint >= 0 ? s:redo_lastline : a:lastline
  let l:is_selection = s:IsVisualSelectionRange(a:uses_range, l:firstline, l:lastline)
  let l:selection = s:GetSelectionOrRange(l:is_selection, a:uses_range, l:firstline, l:lastline)

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
  let s:last_uses_range = a:uses_range
  let s:last_is_selection = l:is_selection
  let s:last_firstline = l:firstline
  let s:last_lastline = l:lastline

  let l:cursor_on_empty_line = empty(getline('.'))
  try
    call s:set_paste(l:config)
    if l:cursor_on_empty_line
      execute "normal! " . l:lastline . "GA"
    else
      execute "normal! " . l:lastline . "Go"
    endif
    py3 run_ai_completition(unwrap('l:context'))
    execute "normal! " . l:lastline . "G"
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
  let l:firstline = s:redo_selection_hint >= 0 ? s:redo_firstline : a:firstline
  let l:lastline = s:redo_selection_hint >= 0 ? s:redo_lastline : a:lastline
  let l:is_selection = s:IsVisualSelectionRange(a:uses_range, l:firstline, l:lastline)
  let l:selection = s:GetSelectionOrRange(l:is_selection, a:uses_range, l:firstline, l:lastline)

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
  let s:last_uses_range = a:uses_range
  let s:last_is_selection = l:is_selection
  let s:last_firstline = l:firstline
  let s:last_lastline = l:lastline

  try
    call s:set_paste(l:config)
    call s:SelectSelectionOrRange(l:is_selection, l:firstline, l:lastline)
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
  let l:firstline = s:redo_selection_hint >= 0 ? s:redo_firstline : a:firstline
  let l:lastline = s:redo_selection_hint >= 0 ? s:redo_lastline : a:lastline
  let l:is_selection = s:IsVisualSelectionRange(a:uses_range, l:firstline, l:lastline)
  let l:selection = s:GetSelectionOrRange(l:is_selection, a:uses_range, l:firstline, l:lastline)

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
  let s:last_uses_range = a:uses_range
  let s:last_is_selection = l:is_selection
  let s:last_firstline = l:firstline
  let s:last_lastline = l:lastline

  py3 run_ai_image(unwrap('l:context'))
endfunction

function! s:ReuseOrCreateChatWindow(config)
  let l:open_conf = a:config['ui']['open_chat_command']

  if a:config['ui']['force_new_chat'] == '1'
    call s:OpenChatWindow(l:open_conf, 1)
    return
  endif

  if &filetype != 'aichat'
    let l:buffer_list_tab = tabpagebuflist(tabpagenr())

    " reuse chat in active tab
    for l:bufnr in l:buffer_list_tab
      if s:StartsWith(bufname(l:bufnr), s:scratch_buffer_name)
        call win_gotoid(bufwinid(l:bufnr))
        return
      endif
    endfor

    " reuse .aichat file on the same tab
    for l:bufnr in l:buffer_list_tab
      if getbufvar(l:bufnr, "&filetype") ==# "aichat"
        call win_gotoid(bufwinid(l:bufnr))
        return
      endif
    endfor

    " open tab local buffer if present
    let l:tab_local_buffer_name = s:GetTabLocalChatBufferNumber()
    if l:tab_local_buffer_name != -1
      call s:OpenChatWindow(l:open_conf, 0)
      return
    endif

    " reuse any .aichat buffer in the session
    let l:open_buffer_list = []
    for i in range(tabpagenr('$'))
      call extend(l:open_buffer_list, tabpagebuflist(i + 1))
    endfor
    for l:bufnr in reverse(sort(l:open_buffer_list))
      if getbufvar(l:bufnr, "&filetype") ==# "aichat"
        call win_gotoid(win_findbuf(l:bufnr)[0])
        return
      endif
    endfor

    " open new chat window if no active buffer found
    call s:OpenChatWindow(l:open_conf, 0)
  endif
endfunction

" Undo history is cluttered when using async chat.
" There doesn't seem to be a way to use standard undojoin feature,
" therefore working around with undoing and pasting changes manually.
function! s:AIChatUndoCleanup()
  let l:bufnr = bufnr()
  let l:done = py3eval("ai_job_pool.is_job_done(unwrap('l:bufnr'))")
  let l:chat_initiation_line = getbufvar(l:bufnr, 'vim_ai_chat_start_last_line', -1)
  let l:undo_cleaned = l:chat_initiation_line == -1
  if !l:done || l:undo_cleaned
    return
  endif

  let l:current_line_num = line('.')
  " navigate to the line where it started generating answer
  execute l:chat_initiation_line
  execute 'normal! j'
  " copy whole assistant message to the `d` register
  execute 'normal! "dyG'
  " undo until user message
  while line('$') > l:chat_initiation_line
    execute "normal! u"
  endwhile
  " paste assistat message as a whole
  execute 'normal! "dp'
  execute l:current_line_num

  call setbufvar(l:bufnr, 'vim_ai_chat_start_last_line', -1)
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

  try
    call s:set_paste(l:config)
    call s:ReuseOrCreateChatWindow(l:config)

    let l:context['bufnr'] = bufnr()
    let l:bufnr = bufnr()

    if py3eval("ai_job_pool.is_job_done(unwrap('l:bufnr'))") == 0
      echoerr "Operation in progress, wait or stop it with :AIStopChat"
      return
    endif

    let s:last_command = "chat"
    let s:last_config = a:config

    if py3eval("run_ai_chat(unwrap('l:context'))")
      if g:vim_ai_async_chat == 1

        call setbufvar(l:bufnr, 'vim_ai_chat_start_last_line', line('$'))
        " if user switches to a different buffer, setup autocommand that
        " will clean undo history after returning back
        augroup AichatUndo
          au!
          autocmd BufEnter <buffer> call s:AIChatUndoCleanup()
        augroup END
        execute "normal! Go\n<<< answering"
        call timer_start(0, function('vim_ai#AIChatWatch', [l:bufnr, 0]))
      endif
    endif
  finally
    call s:set_nopaste(l:config)
  endtry
endfunction

" Stop current chat job
function! vim_ai#AIChatStopRun() abort
  if &filetype !=# 'aichat'
    echoerr "Not in an AI chat buffer."
    return
  endif
  let l:bufnr = bufnr('%')
  call s:ImportPythonModules() " Ensure chat.py is loaded
  py3 ai_job_pool.cancel_job(unwrap('l:bufnr'))
  call s:AIChatUndoCleanup()
endfunction


" Function called in a timer that check if there are new lines from AI and
" appned them in a buffer. It ends when AI thread is finished (or when
" stopped).
function! vim_ai#AIChatWatch(bufnr, anim_index, timerid) abort
  " inject new lines, first check if it is done to avoid data race, we do not
  " mind if we run the timer one more time, but we want all the data
  let l:done = py3eval("ai_job_pool.is_job_done(unwrap('a:bufnr'))")
  let l:result = py3eval("ai_job_pool.pickup_lines(unwrap('a:bufnr'))")

  " if user scroling over chat while answering, do not auto-scroll
  let l:should_prevent_autoscroll = bufnr('%') == a:bufnr && line('.') != line('$')

  call deletebufline(a:bufnr, '$')
  call deletebufline(a:bufnr, '$')
  call appendbufline(a:bufnr, '$', l:result)

  " if not done, queue timer and animate
  if l:done == 0
    call timer_start(s:chat_redraw_interval, function('vim_ai#AIChatWatch', [a:bufnr, a:anim_index + 1]))
    call appendbufline(a:bufnr, '$', "")
    let l:animations = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
    let l:current_animation = l:animations[a:anim_index % len(l:animations)]
    call appendbufline(a:bufnr, '$', "<<< answering " . l:current_animation)
  else
    call s:AIChatUndoCleanup()
    " Clear message
    " https://neovim.discourse.group/t/how-to-clear-the-echo-message-in-the-command-line/268/3
    call feedkeys(':','nx')
  end

  " if window is visible and user not scrolling, auto-scroll down
  let winid = bufwinid(a:bufnr)
  if winid != -1 && !l:should_prevent_autoscroll
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
  let s:redo_selection_hint = s:last_is_selection
  let s:redo_firstline = s:last_firstline
  let s:redo_lastline = s:last_lastline
  try
    if s:last_command ==# "complete"
      call vim_ai#AIRun(s:last_uses_range, s:last_config, s:last_instruction)
    elseif s:last_command ==# "edit"
      call vim_ai#AIEditRun(s:last_uses_range, s:last_config, s:last_instruction)
    elseif s:last_command ==# "image"
      call vim_ai#AIImageRun(s:last_uses_range, s:last_config, s:last_instruction)
    elseif s:last_command ==# "chat"
      " chat does not need prompt, all information are in the buffer already
      call vim_ai#AIChatRun(0, s:last_config)
    endif
  finally
    let s:redo_selection_hint = -1
    let s:redo_firstline = 1
    let s:redo_lastline = 1
  endtry
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
