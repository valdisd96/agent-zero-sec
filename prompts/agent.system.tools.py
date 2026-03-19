import os
from typing import Any
from python.helpers.files import VariablesPlugin
from python.helpers import files
from python.helpers.print_style import PrintStyle


class BuidToolsPrompt(VariablesPlugin):
    def get_variables(self, file: str, backup_dirs: list[str] | None = None, **kwargs) -> dict[str, Any]:

        # collect all prompt folders in order of their priority
        folder = files.get_abs_path(os.path.dirname(file))
        folders = [folder]
        if backup_dirs:
            for backup_dir in backup_dirs:
                folders.append(files.get_abs_path(backup_dir))

        # collect all tool instruction files
        prompt_files = files.get_unique_filenames_in_dirs(folders, "agent.system.tool.*.md")

        # DEBUG: log tool prompt files being loaded per agent
        agent = kwargs.get("_agent", None)
        agent_label = f"Agent #{agent.number} ({agent.config.profile})" if agent else "Unknown agent"
        tool_names = [os.path.basename(pf) for pf in prompt_files]
        PrintStyle().print(f"\n[DEBUG TOOLS] {agent_label} — {len(tool_names)} tool prompts loaded:")
        for tn in sorted(tool_names):
            PrintStyle().print(f"  - {tn}")

        # load tool instructions
        tools = []
        for prompt_file in prompt_files:
            try:
                tool = files.read_prompt_file(prompt_file, **kwargs)
                tools.append(tool)
            except Exception as e:
                PrintStyle().error(f"Error loading tool '{prompt_file}': {e}")

        return {"tools": "\n\n".join(tools)}
