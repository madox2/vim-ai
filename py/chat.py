import vim
import threading
import time
import copy
import json
import traceback
import re
from extensions import MCPManager

chat_py_imported = True

TOOLS_DESCRIPTION = """
To perform actions, you MUST use the following format:
```tool
{
  "tool": "tool_name",
  "arguments": { "arg1": "val1" }
}
```

Available tools:
- bash(command: str): Run a shell command.
- read_file(path: str, max_line: int = -1): Read file contents.
- write_file(path: str, content: str): Write content to file.
- edit_file(path: str, old_text: str, new_text: str): Replace exact text in file.

If you are providing a JSON example for the user, use standard ```json blocks. Only use ```tool for actual execution.
"""

def _populate_options(provider, options, default_options, show_default = False):
    vim.command("normal! O[chat]")
    vim.command("normal! o")
    vim.command("normal! iprovider=" + provider + "\n")
    for key, value in options.items():
        default_value = default_options.get(key, '')
        if key == 'initial_prompt':
            value = "\\n".join(value)
            default_value = "\\n".join(default_value)

        if not show_default and default_value == value:
            continue # do not show default values

        if not isinstance(value, str):
            value = str(value)

        vim.command("normal! ioptions." + key + "=" + value + "\n")

def run_ai_chat(context):
    update_thread_shared_variables()
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
        populate = not '[chat]' in lines and (config['ui']['populate_options'] == '1' or config['ui']['populate_all_options'] == '1')
        # when called special `populate` role, force chat header re-population
        re_populate = 'populate' in roles or 'populate-all' in roles
        is_populating_all = 'populate-all' in roles or config['ui']['populate_all_options'] == '1'

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

            default_config = make_config(vim.eval('g:vim_ai_chat_default'))
            default_options = default_config['options']

            if is_populating_all:
                # get default options from the provider if available
                provider_class = load_provider(config['provider'])
                default_provider_options = {}
                # backward compatibility, provider does not have to implement it or it is empty
                if hasattr(provider_class, "default_options_varname_chat") and provider_class.default_options_varname_chat:
                    default_provider_options = make_options(vim.eval(provider_class.default_options_varname_chat))

                populated_options = {**default_options, **default_provider_options, **config['options']}
                _populate_options(config['provider'], populated_options, {}, show_default = True)
            else:
                _populate_options(config['provider'], config['options'], default_options, show_default = False)


        vim.command("normal! G")
        vim_break_undo_sequence()
        vim.command("redraw")

        last_role = re.match(r".*^(>>>|<<<) (\w+)", file_content, flags=re.DOTALL | re.MULTILINE)
        if last_role and last_role.group(2) not in ('user', 'include', 'exec', 'info'):
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

    # Inject tools description if it's a chat
    if command_type == 'chat':
        tools_msg = TOOLS_DESCRIPTION
        if initial_messages and initial_messages[0]['role'] == 'system':
            initial_messages[0]['content'][0]['text'] += "\n\n" + tools_msg
        else:
            initial_messages.insert(0, {'role': 'system', 'content': [{'type': 'text', 'text': tools_msg}]})

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
                previous_type = ""

                def _chunks_to_sections(chunks):
                    nonlocal previous_type
                    for chunk in chunks:
                        if previous_type != chunk["type"] or "newsegment" in chunk:
                            vim.command(f"normal! Go\n<<< {chunk['type']}\n\n")
                            previous_type = chunk["type"]
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
        self.mcp_manager = MCPManager()

    def run(self):
        print_debug("AI_chat_job thread STARTED")
        tool_map = {
            "bash": run_bash,
            "read_file": run_read,
            "write_file": run_write,
            "edit_file": run_edit,
        }
        try:
            loop_count = 0
            while loop_count < 10 and not self.cancelled:
                loop_count += 1
                full_response = ""
                for chunk in self.provider.request(self.messages):
                    with self.lock:
                        if self.previous_type != chunk["type"] or "newsegment" in chunk:
                            if self.previous_type != "":
                                self.buffer += "\n"
                            self.buffer += "\n<<< " + chunk["type"] + "\n\n"
                            self.previous_type = chunk["type"]
                        self.buffer += chunk["content"]
                        full_response += chunk["content"]
                        if self.cancelled:
                            self.buffer += "\n\nCANCELLED by user"
                            break
                        if "\n" in self.buffer:
                            parts = self.buffer.split("\n")
                            self.lines.extend(parts[:-1])
                            self.buffer = parts[-1]

                if self.cancelled:
                    break

                self.messages.append({"role": "assistant", "content": [{"type": "text", "text": full_response}]})

                # call the tools if there are any calls in the response
                tool_calls = re.findall(r"```(?:tool|json)\n(.*?)\n```", full_response, re.DOTALL)
                if not tool_calls:
                    break

                executed_any = False
                results = []
                for call_str in tool_calls:
                    try:
                        call = json.loads(call_str)
                        if not isinstance(call, dict) or "tool" not in call:
                            continue

                        tool_name = call.get("tool")
                        args = call.get("arguments", {})

                        with self.lock:
                            self.lines.append(self.buffer)
                            self.buffer = f"\n>>> exec\n\n{tool_name}: {json.dumps(args)}"
                            self.previous_type = "exec"

                        if tool_name in tool_map:
                            output = tool_map[tool_name](**args)
                        else:
                            output = self.mcp_manager.execute(tool_name, **args)

                        results.append(f"Tool '{tool_name}' output:\n{output}")
                        executed_any = True

                        with self.lock:
                            self.lines.append(self.buffer)
                            self.buffer = f"\n{output}\n"

                    except Exception as e:
                        print_debug(f"Tool execution failed: {e}")
                        continue

                if not executed_any:
                    break

                tool_results_content = "\n\n".join(results)
                self.messages.append({"role": "user", "content": [{"type": "text", "text": tool_results_content}]})
                
                with self.lock:
                    self.lines.append(self.buffer)
                    self.buffer = "\n>>> user\n\n(Agent feedback received, thinking...)\n"
                    self.previous_type = "user"

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
            self.mcp_manager.shutdown()
        print_debug("AI_chat_job thread DONE")

    def pickup_lines(self):
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
        self.pool[bufnr] = AI_chat_job(context, messages, provider)
        self.pool[bufnr].start()
        return self.pool[bufnr]

    # pickup lines from a job based on bufnr
    def pickup_lines(self, bufnr):
        if bufnr in self.pool:
            return self.pool[bufnr].pickup_lines()
        return []

    def is_job_done(self, bufnr):
        if bufnr in self.pool:
            return self.pool[bufnr].is_done()
        return True

    def cancel_job(self, bufnr):
        print_debug(f"Attempting to cancel job for bufnr {bufnr}")
        if bufnr in self.pool:
            job = self.pool[bufnr]
            if not job.is_done():
                job.cancel()
                print_debug(f"Cancellation signal sent to job for bufnr {bufnr}")
                return True
            else:
                print_debug(f"Job for bufnr {bufnr} is already done.")
                return False
        print_debug(f"No active job found for bufnr {bufnr} to cancel.")
        return False

ai_job_pool = AI_chat_jobs_pool()
