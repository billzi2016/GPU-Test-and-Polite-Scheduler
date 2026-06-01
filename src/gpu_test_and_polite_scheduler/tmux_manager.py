from __future__ import annotations

"""tmux 操作封装。

这里故意把所有 tmux 命令收口到一个文件里，原因是后续如果要从
`tmux` 切到 `screen`、systemd-run 或更复杂的运行器，影响面会更小。
"""

from dataclasses import dataclass

from .utils import append_log_redirection, run_command


@dataclass
class TmuxCommandResult:
    code: int
    stdout: str
    stderr: str


class TmuxManager:
    """对 tmux 子命令做最小但稳定的封装。"""

    def has_session(self, session_name: str) -> bool:
        # session 是否存在，是 watchdog 判断任务是否还活着的最小依据。
        result = self._run(["tmux", "has-session", "-t", session_name])
        return result.code == 0

    def create_session(self, session_name: str, command: str | None = None, workdir: str | None = None) -> TmuxCommandResult:
        """创建一个后台 session。

        这里不直接在 `new-session` 里塞完整业务命令，而是优先起一个 shell，
        再通过 `send-keys` 注入命令。这样更接近日常手工使用 tmux 的方式，
        也更容易在后续追加环境变量、日志重定向或调试命令。
        """

        shell_command = command or "bash"
        # 先切到指定工作目录再执行命令，避免任务依赖相对路径时出错。
        target_command = shell_command if workdir is None else f"cd {workdir} && {shell_command}"
        return self._run(["tmux", "new-session", "-d", "-s", session_name, target_command])

    def kill_session(self, session_name: str) -> TmuxCommandResult:
        return self._run(["tmux", "kill-session", "-t", session_name])

    def send_command(self, session_name: str, command: str, log_file: str | None = None) -> TmuxCommandResult:
        # `send-keys ... C-m` 的本质是“向这个 tmux pane 模拟输入一行命令并回车”。
        final_command = append_log_redirection(command, log_file)
        return self._run(["tmux", "send-keys", "-t", session_name, final_command, "C-m"])

    def restart_session(
        self,
        session_name: str,
        command: str,
        workdir: str | None = None,
        log_file: str | None = None,
    ) -> None:
        # 统一用“杀掉旧 session 后重建”的方式，避免同名 session 里残留旧状态。
        # 这样做的代价是更粗暴，但好处是状态机简单，不容易出现“以为已经重启，
        # 实际只是向旧 shell 又发了一次命令”的隐性重复执行问题。
        if self.has_session(session_name):
            self.kill_session(session_name)
        create_result = self.create_session(session_name, workdir=workdir)
        if create_result.code != 0:
            raise RuntimeError(create_result.stderr or f"failed to create session {session_name}")
        send_result = self.send_command(session_name, command, log_file=log_file)
        if send_result.code != 0:
            raise RuntimeError(send_result.stderr or f"failed to send command to {session_name}")

    def _run(self, command: list[str]) -> TmuxCommandResult:
        # 统一返回结构，避免上层每次自己处理 code/stdout/stderr 三元组。
        code, stdout, stderr = run_command(command)
        return TmuxCommandResult(code=code, stdout=stdout, stderr=stderr)
