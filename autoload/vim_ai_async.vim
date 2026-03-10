function! vim_ai_async#EnablePasteMode(config) abort
  if !&l:paste && a:config['ui']['paste_mode'] == '1'
    setlocal paste
    let b:vim_ai_async_restore_paste = 1
  endif
endfunction

function! vim_ai_async#DisablePasteMode() abort
  if get(b:, 'vim_ai_async_restore_paste', 0)
    setlocal nopaste
    unlet b:vim_ai_async_restore_paste
  endif
endfunction

function! vim_ai_async#DisablePasteModeForBuffer(bufnr) abort
  if getbufvar(a:bufnr, 'vim_ai_async_restore_paste', 0)
    call setbufvar(a:bufnr, '&paste', 0)
    call setbufvar(a:bufnr, 'vim_ai_async_restore_paste', 0)
  endif
endfunction

" Undo history is cluttered when using async chat.
" There doesn't seem to be a way to use standard undojoin feature,
" therefore working around with undoing and pasting changes manually.
function! vim_ai_async#AIChatUndoCleanup() abort
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
    execute 'normal! u'
  endwhile
  " paste assistat message as a whole
  execute 'normal! "dp'
  execute l:current_line_num

  call setbufvar(l:bufnr, 'vim_ai_chat_start_last_line', -1)
endfunction

" Stop current chat job
function! vim_ai_async#AIChatStopRun() abort
  if &filetype !=# 'aichat'
    echoerr 'Not in an AI chat buffer.'
    return
  endif
  let l:bufnr = bufnr('%')
  call vim_ai#ImportPythonModules()
  py3 ai_job_pool.cancel_job(unwrap('l:bufnr'))
  call vim_ai_async#AIChatUndoCleanup()
endfunction

" Function called in a timer that check if there are new lines from AI and
" appned them in a buffer. It ends when AI thread is finished (or when
" stopped).
function! vim_ai_async#AIChatWatch(bufnr, anim_index, timerid) abort
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
    call timer_start(250, function('vim_ai_async#AIChatWatch', [a:bufnr, a:anim_index + 1]))
    call appendbufline(a:bufnr, '$', '')
    let l:animations = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
    let l:current_animation = l:animations[a:anim_index % len(l:animations)]
    call appendbufline(a:bufnr, '$', '<<< answering ' . l:current_animation)
  else
    call vim_ai_async#AIChatUndoCleanup()
    " Clear message
    " https://neovim.discourse.group/t/how-to-clear-the-echo-message-in-the-command-line/268/3
    call feedkeys(':','nx')
  end

  " if window is visible and user not scrolling, auto-scroll down
  let winid = bufwinid(a:bufnr)
  if winid != -1 && !l:should_prevent_autoscroll
    call win_execute(winid, 'normal! G')
  endif
endfunction

" Stop current completion/edit job
function! vim_ai_async#AIStopRun() abort
  call vim_ai#ImportPythonModules()
  let l:bufnr = bufnr('%')
  if py3eval("ai_completion_job_pool.is_job_done(unwrap('l:bufnr'))")
    echoerr 'No async :AI or :AIEdit task is running.'
    return
  endif
  py3 ai_completion_job_pool.cancel_job(unwrap('l:bufnr'))
endfunction

" Function called in a timer to insert async completion chunks.
function! vim_ai_async#AICompletionWatch(bufnr, timerid) abort
  let l:done = py3eval("apply_ai_completion_job(unwrap('a:bufnr'))")
  if l:done == 0
    call timer_start(150, function('vim_ai_async#AICompletionWatch', [a:bufnr]))
  else
    call vim_ai_async#DisablePasteModeForBuffer(a:bufnr)
  endif
endfunction
