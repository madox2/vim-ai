import json
import shutil
import subprocess
import tempfile
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]


def _find_vim():
    return shutil.which("vim") or shutil.which("nvim")


def _run_headless_vim(script):
    vim_bin = _find_vim()
    if vim_bin is None:
        pytest.skip("vim or nvim executable not available")

    with tempfile.TemporaryDirectory() as tmpdir:
        script_path = Path(tmpdir) / "test.vim"
        script_path.write_text(script, encoding="utf-8")
        subprocess.run(
            [vim_bin, "-Nu", "NONE", "-nEs", "-S", str(script_path)],
            check=True,
            cwd=REPO_ROOT,
        )


def test_visual_selection_detection_does_not_leak_into_explicit_ranges():
    with tempfile.TemporaryDirectory() as tmpdir:
        out_path = Path(tmpdir) / "result.txt"
        repo = str(REPO_ROOT).replace("'", "''")
        out = str(out_path).replace("'", "''")
        script = f"""
set nocompatible
set nomore
set shortmess+=I
set rtp^={repo}
call vim_ai#AIUtilSetDebug(0)

new
call setline(1, ['Lorem ipsum dolor sit amet.'])
call setpos("'<", [0, 1, 1, 0])
call setpos("'>", [0, 1, 5, 0])

let explicit_range_result = vim_ai#IsVisualSelectionRange(1, 1, 1, '.Probe')

let visual_range_result = vim_ai#IsVisualSelectionRange(1, 1, 1, "'<,'>Probe")

call writefile([string(explicit_range_result), string(visual_range_result)], '{out}')
qa!
"""
        _run_headless_vim(script)

        results = out_path.read_text(encoding="utf-8").splitlines()
        assert results == ["0", "1"]


def test_redo_preserves_explicit_range_for_image_commands():
    with tempfile.TemporaryDirectory() as tmpdir:
        out_path = Path(tmpdir) / "result.txt"
        repo = str(REPO_ROOT).replace("'", "''")
        out = str(out_path).replace("'", "''")
        script = f"""
set nocompatible
set nomore
set shortmess+=I
set rtp^={repo}
call vim_ai#AIUtilSetDebug(0)

py3 << PY
import json
from pathlib import Path
import vim
records = []
for name in ['types', 'utils', 'context', 'chat', 'complete', 'roles', 'image']:
    globals()[f'{{name}}_py_imported'] = True

def unwrap(expr):
    return vim.eval(expr)

def make_ai_context(config_input):
    records.append({{
        'user_selection': config_input['user_selection'],
        'is_selection': config_input['is_selection'],
        'command_type': config_input['command_type'],
    }})
    return {{'config': {{'ui': {{'paste_mode': '0'}}}}, 'prompt': ''}}

def run_ai_image(context):
    pass
PY

new
call setline(1, ['abcdef', 'ghijkl'])
1,1call vim_ai#AIImageRun(2, {{}}, '')
normal! G
call vim_ai#AIRedoRun()
py3 Path('{out}').write_text(json.dumps(records), encoding='utf-8')
qa!
"""
        _run_headless_vim(script)

        results = json.loads(out_path.read_text(encoding="utf-8"))
        assert results == [
            {
                "user_selection": "abcdef",
                "is_selection": "0",
                "command_type": "image",
            },
            {
                "user_selection": "abcdef",
                "is_selection": "0",
                "command_type": "image",
            },
        ]
