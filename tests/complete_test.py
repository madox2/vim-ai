from types import SimpleNamespace

import complete


class FakeVim:
    def __init__(self, buffers):
        self.buffers = buffers
        self.commands = []

    def command(self, cmd):
        self.commands.append(cmd)


def make_job(chunks, done=False):
    return SimpleNamespace(
        render_state={
            'started': False,
            'full_text': '',
            'insert_before_cursor': False,
            'append_to_eol': True,
            'row': 0,
            'col': 0,
        },
        error=None,
        cancelled=False,
        provider_name='openai',
        pickup_chunks=lambda: chunks,
        is_done=lambda: done,
    )


def test_apply_ai_completion_job_redraws_after_chunk_render(monkeypatch):
    fake_vim = FakeVim({1: ['hello ']})
    job = make_job(['world'], done=False)
    monkeypatch.setattr(complete, 'vim', fake_vim)
    monkeypatch.setattr(complete.ai_completion_job_pool, 'get_job', lambda _: job)

    done = complete.apply_ai_completion_job(1)

    assert done is False
    assert fake_vim.buffers[1] == ['hello world']
    assert fake_vim.commands == ['redraw']
