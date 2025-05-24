import vim
import threading
import time
import copy
import json
import traceback

chat_py_imported = True

def _populate_options(config):
    default_config = make_config(vim.eval('g:vim_ai_chat_default'))

    default_options = default_config['options']
    options = config['options']

    vim.command("normal! O[chat]")
    vim.command("normal! o")
    vim.command("normal! iprovider=" + config['provider'] + "\n")
    for key, value in options.items():
        default_value = default_options.get(key, '')
        if key == 'initial_prompt':
            value = "\\n".join(value)
            if default_value:
                default_value = "\\n".join(default_value)

        if default_value == value:
            continue # do not show default values
        vim.command("normal! ioptions." + key + "=" + value + "\n")

def run_ai_chat(context):
    command_type = context['command_type']
    prompt = context['prompt']
    config = make_config(context['config'])
    config_options = config['options']
    roles = context['roles']
    started_from_chat = context['started_from_chat'] == '1'

    def initialize_chat_window():
        file_content = vim.eval('trim(join(getline(1, "$"), "\n"))')
        contains_user_prompt = re.search(r"^>>> (user|exec|include)", file_content, flags=re.MULTILINE)
        lines = vim.eval('getline(1, "$")')

        # if populate is set in config, populate once
        # it shouldn't re-populate after chat header options are modified (#158)
        populate = config['ui']['populate_options'] == '1' and not '[chat]' in lines
        # when called special `populate` role, force chat header re-population
        re_populate = 'populate' in roles

        if re_populate:
            if '[chat]' in lines:
                line_num = lines.index('[chat]') + 1
                vim.command("normal! " + str(line_num) + "gg")
                vim.command("normal! d}dd")

        if not contains_user_prompt:
            # user role not found, put whole file content as an user prompt
            vim.command("normal! gg")
            vim.command("normal! O>>> user\n")

        if populate or re_populate:
            vim.command("normal! gg")
            _populate_options(config)

        vim.command("normal! G")
        vim_break_undo_sequence()
        vim.command("redraw")

        last_role = re.match(r".*^(>>>|<<<) (\w+)", file_content, flags=re.DOTALL | re.MULTILINE)
        if last_role and last_role.group(2) not in ('user', 'include', 'exec', 'tool_call', 'tool_response', 'info'):
            # last role is not a user role, most likely completion was cancelled before
            vim.command("normal! o")
            vim.command("normal! i\n>>> user\n\n")

        if prompt:
            vim.command("normal! dd")
            vim.current.buffer.append(prompt.splitlines())
            vim_break_undo_sequence()
            vim.command("normal! G")
            vim.command("redraw")

    initialize_chat_window()

    chat_config = parse_chat_header_config()
    options = {**config_options, **chat_config['options']}
    provider = chat_config['provider'] or config['provider']

    initial_prompt = '\n'.join(options.get('initial_prompt', []))
    initial_messages = parse_chat_messages(initial_prompt)

    chat_content = vim.eval('trim(join(getline(1, "$"), "\n"))')
    print_debug(f"[{command_type}] text:\n" + chat_content)
    chat_messages = parse_chat_messages(chat_content)

    messages = initial_messages + chat_messages

    try:
        last_content = messages[-1]["content"][-1]

        # if empty :AIC has been called outside of the chat, just init/switch to the chat but don't trigger the request (#147)
        should_imediately_answer = prompt or started_from_chat
        awaiting_response = last_content['type'] != 'text' or last_content['text'] or "tool_calls" in messages[-1]
        if awaiting_response and should_imediately_answer:
            vim.command("redraw")

            print('Answering...')
            vim.command("redraw")
            provider_class = load_provider(provider)
            provider = provider_class(command_type, options, ai_provider_utils)

            if vim.eval("g:vim_ai_async_chat") == "1":
                ai_job_pool.new_job(context, messages, provider)
            else:
                response_chunks = provider.request(messages)

                def _chunks_to_sections(chunks):
                    first_thinking_chunk = True
                    first_content_chunk = True
                    for chunk in chunks:
                        if chunk['type'] == 'thinking' and first_thinking_chunk:
                            first_thinking_chunk = False
                            vim.command("normal! Go\n<<< thinking\n\n")
                        if chunk['type'] == 'assistant' and first_content_chunk:
                            first_content_chunk = False
                            vim.command("normal! Go\n<<< assistant\n\n")
                        yield chunk['content']

                render_text_chunks(_chunks_to_sections(response_chunks), append_to_eol=True)

                vim.command("normal! a\n\n>>> user\n\n")
                vim.command("redraw")
                clear_echo_message()

            return True
        else:
            return False
    except BaseException as error:
        handle_completion_error(provider, error)
        print_debug("[{}] error: {}", command_type, traceback.format_exc())


# wraps the AI chat job, shall be unique to a buffer
class AI_chat_job(threading.Thread):
    def __init__(self, context, messages, provider):
        threading.Thread.__init__(self)
        self.lines = []
        self.buffer = ""
        self.previous_type = ""
        self.messages = messages
        self.context = context
        self.cancelled = False
        self.provider = provider
        self.done = False
        self.lock = threading.RLock()

    def run(self):
        print_debug_threaded("AI_chat_job thread STARTED")
        try:
            for chunk in self.provider.request(self.messages):
                with self.lock:
                    # For now, we only append whole lines to the buffer
                    print_debug_threaded(f"Received chunk: '{chunk["type"]}' => '{chunk["content"]}'")
                    if self.previous_type != chunk["type"] or "newsegment" in chunk:
                        if self.previous_type != "":
                            self.buffer += "\n"
                        self.buffer += "\n<<< " + chunk["type"] + "\n\n"
                        self.previous_type = chunk["type"]
                    self.buffer += chunk["content"]
                    if self.cancelled:
                        self.buffer += "\n\nCANCELLED by user"
                        print_debug_threaded("AI_chat_job cancelled during provider request")
                    if "\n" in self.buffer:
                        parts = self.buffer.split("\n")
                        self.lines.extend(parts[:-1])
                        self.buffer = parts[-1]
                    if self.cancelled:
                        break # Exit the loop
        except Exception as e:
            with self.lock:
                self.lines.append("")
                self.lines.append(f"<<< error getting response: {str(e)}")
                self.lines.append("")
                self.lines.append("```python")
                self.lines.extend(traceback.format_exc().split("\n"))
                self.lines.append("```")
                try:
                    self.lines.append("")
                    self.lines.append(json.loads(e.read().decode())["error"]["message"])
                except:
                    pass
        finally:
            with self.lock:
                self.lines.append(self.buffer)
                if self.previous_type == "assistant":
                    self.lines.extend("\n>>> user\n\n".split("\n"))
                self.done = True
        print_debug_threaded("AI_chat_job thread DONE")

    def pickup(self):
        with self.lock:
            lines = copy.deepcopy(self.lines)
            self.lines = []
        return lines

    def is_done(self):
        with self.lock:
            done = self.done
        return done

    def cancel(self):
        with self.lock:
            self.cancelled = True

# Pool of AI chat jobs accessible by bufnr
# There can be only one in progress per bufnr
class AI_chat_jobs_pool(object):
    def __init__(self):
        self.pool = {}

    def new_job(self, context, messages, provider):
        bufnr = context["bufnr"]
        update_debug_variables()
        self.pool[bufnr] = AI_chat_job(context, messages, provider)
        self.pool[bufnr].start()
        return self.pool[bufnr]

    # pickup lines from a job based on bufnr
    def pickup_lines(self, bufnr):
        if bufnr in self.pool:
            lines = self.pool[bufnr].pickup()
            ret = []
            for line in lines:
                ret.append(line)
            return ret
        else:
            return []

    def is_job_done(self, bufnr):
        if bufnr in self.pool:
            if self.pool[bufnr].is_done():
                return 1
            return 0
        else:
            return 1

    def cancel_job(self, bufnr):
        print_debug_threaded(f"Attempting to cancel job for bufnr {bufnr}")
        if bufnr in self.pool:
            job = self.pool[bufnr]
            if not job.is_done():
                job.cancel()
                print_debug_threaded(f"Cancellation signal sent to job for bufnr {bufnr}")
                return True
            else:
                print_debug_threaded(f"Job for bufnr {bufnr} is already done.")
                return False
        print_debug_threaded(f"No active job found for bufnr {bufnr} to cancel.")
        return False

ai_job_pool = AI_chat_jobs_pool()
