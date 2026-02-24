import vim
import copy
import threading
import traceback

complete_py_imported = True

class AI_completion_job(threading.Thread):
    def __init__(self, bufnr, messages, provider, provider_name, append_to_eol, insert_before_cursor, row, col):
        threading.Thread.__init__(self)
        self.bufnr = bufnr
        self.messages = messages
        self.provider = provider
        self.provider_name = provider_name
        self.append_to_eol = append_to_eol
        self.insert_before_cursor = insert_before_cursor
        self.chunks = []
        self.cancelled = False
        self.done = False
        self.error = None
        self.render_state = {
            'started': False,
            'full_text': '',
            'insert_before_cursor': insert_before_cursor,
            'append_to_eol': append_to_eol,
            'row': row,
            'col': col,
        }
        self.lock = threading.RLock()

    def run(self):
        print_debug("AI_completion_job thread STARTED")
        try:
            for chunk in self.provider.request(self.messages):
                with self.lock:
                    if self.cancelled:
                        break
                    if chunk.get('type') != 'assistant':
                        continue
                    content = chunk.get('content')
                    if content:
                        self.chunks.append(content)
        except Exception as e:
            with self.lock:
                self.error = e
        finally:
            with self.lock:
                self.done = True
        print_debug("AI_completion_job thread DONE")

    def pickup_chunks(self):
        with self.lock:
            chunks = copy.deepcopy(self.chunks)
            self.chunks = []
        return chunks

    def is_done(self):
        with self.lock:
            done = self.done
        return done

    def cancel(self):
        with self.lock:
            self.cancelled = True

class AI_completion_jobs_pool(object):
    def __init__(self):
        self.pool = {}

    def new_job(self, bufnr, messages, provider, provider_name, append_to_eol, insert_before_cursor, row, col):
        bufnr = int(bufnr)
        self.pool[bufnr] = AI_completion_job(
            bufnr,
            messages,
            provider,
            provider_name,
            append_to_eol,
            insert_before_cursor,
            row,
            col,
        )
        self.pool[bufnr].start()
        return self.pool[bufnr]

    def get_job(self, bufnr):
        return self.pool.get(int(bufnr))

    def pickup_chunks(self, bufnr):
        job = self.pool.get(int(bufnr))
        return job.pickup_chunks() if job else []

    def is_job_done(self, bufnr):
        job = self.pool.get(int(bufnr))
        return job.is_done() if job else True

    def cancel_job(self, bufnr):
        job = self.pool.get(int(bufnr))
        if not job:
            return False
        if not job.is_done():
            job.cancel()
            return True
        return False

ai_completion_job_pool = AI_completion_jobs_pool()

def _insert_text_into_buffer(buffer, row, col, text):
    lines = text.split("\n")
    current_line = buffer[row]
    before = current_line[:col]
    after = current_line[col:]
    if len(lines) == 1:
        buffer[row] = before + lines[0] + after
        return row, col + len(lines[0])

    new_lines = [before + lines[0]]
    if len(lines) > 2:
        new_lines.extend(lines[1:-1])
    new_lines.append(lines[-1] + after)
    buffer[row:row + 1] = new_lines
    return row + len(new_lines) - 1, len(lines[-1])

def _render_text_chunks_incremental(bufnr, chunks, state):
    if not chunks:
        return
    buffer = vim.buffers[int(bufnr)]
    for text in chunks:
        if not state['started']:
            text = text.lstrip()
        if not text:
            continue
        state['started'] = True
        row = state['row']
        col = state['col']
        if state['append_to_eol']:
            col = len(buffer[row])
        elif state['insert_before_cursor']:
            col = max(col - 1, 0)
            state['insert_before_cursor'] = False
        row, col = _insert_text_into_buffer(buffer, row, col, text)
        state['row'] = row
        state['col'] = col
        state['full_text'] += text

def apply_ai_completion_job(bufnr):
    bufnr = int(bufnr)
    job = ai_completion_job_pool.get_job(bufnr)
    if not job:
        return True

    chunks = job.pickup_chunks()
    if chunks:
        _render_text_chunks_incremental(bufnr, chunks, job.render_state)

    done = job.is_done()
    if done:
        if job.error:
            handle_completion_error(job.provider_name, job.error)
        elif job.cancelled:
            print_info_message("Completion cancelled...")
        elif not job.render_state['full_text'].strip():
            handle_completion_error(
                job.provider_name,
                KnownError('Empty response received. Tip: You can try modifying the prompt and retry.'),
            )
        clear_echo_message()
    return done


def run_ai_completition(context):
    update_thread_shared_variables()
    command_type = context['command_type']
    prompt = context['prompt']
    config = make_config(context['config'])
    config_options = config['options']
    roles = context['roles']

    try:
        if 'engine' in config and config['engine'] == 'complete':
            raise KnownError('complete engine is no longer supported')

        if prompt or roles:
            print('Completing...')
            vim.command("redraw")

            initial_prompt = config_options.get('initial_prompt', [])
            initial_prompt = '\n'.join(initial_prompt)
            chat_content = f"{initial_prompt}\n\n>>> user\n\n{prompt}".strip()
            messages = parse_chat_messages(chat_content)
            print_debug(f"[{command_type}] text:\n" + chat_content)

            provider_class = load_provider(config['provider'])
            provider = provider_class(command_type, config_options, ai_provider_utils)

            if vim.eval('g:vim_ai_async_complete') == '1':
                cursor_pos = vim.eval("getpos('.')")
                row = int(cursor_pos[1]) - 1
                col = int(cursor_pos[2])
                ai_completion_job_pool.new_job(
                    int(context['bufnr']),
                    messages,
                    provider,
                    config['provider'],
                    command_type == 'complete',
                    need_insert_before_cursor(),
                    row,
                    col,
                )
            else:
                response_chunks = provider.request(messages)

                text_chunks = map(
                    lambda c: c.get('content'),
                    filter(lambda c: c['type'] == 'assistant', response_chunks),
                )

                render_text_chunks(text_chunks, append_to_eol=command_type == 'complete')

                clear_echo_message()
            return True
        return False
    except BaseException as error:
        handle_completion_error(config['provider'], error)
        print_debug("[{}] error: {}", command_type, traceback.format_exc())
        return False
