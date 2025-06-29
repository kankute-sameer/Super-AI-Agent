# agent_tools.py
"""Utility module providing Agent Management, Messaging, and File System tools.

Each function mirrors the signature and behavior requested. Agent-related state is
kept in an in-memory dictionary; message tools are stubs you can integrate with
real notification services later. File system tools wrap the Python standard
library with basic error handling.
"""

from __future__ import annotations

import os
import shutil
import smtplib
from email.message import EmailMessage
from pathlib import Path
from typing import List, Dict, Optional
from datetime import datetime
from agents import function_tool
from pydantic import BaseModel
import requests


###############################################################################
# Agent‑level state (kept simple & in‑memory for illustration)                #
###############################################################################

_agent_state: Dict[str, Optional[object]] = {
    "current_phase_id": None,
    "goal": None,
    "phases": [],
    "completed": False,
    "scheduled_tasks": [],  # list of dicts
}

# Tool description map for logging and UI feedback
tool_description_map = {
    "file_write": lambda args: f"Creating file {args.get('path')}",
    "file_replace_text": lambda args: f"Editing file {args.get('path')}",
    "file_append_text": lambda args: f"Adding content to file {args.get('path')}",
    "file_delete": lambda args: f"Deleting file {args.get('path')}",
    "file_read": lambda args: f"Reading file {args.get('file')}",
    "file_list": lambda args: f"Listing contents of directory {args.get('path')}",
    "file_make_dir": lambda args: f"Creating directory {args.get('path')}",
    "file_copy": lambda args: f"Copying {args.get('source')} to {args.get('destination')}",
    "file_move": lambda args: f"Moving {args.get('source')} to {args.get('destination')}",
    "agent_update_plan": lambda args: "Updating task plan",
    "agent_advance_phase": lambda args: f"Advancing from phase {args.get('from_phase_id')} to {args.get('to_phase_id')}",
    "agent_end_task": lambda args: "Ending current task",
    "agent_schedule_task": lambda args: f"Scheduling task: {args.get('task_description')}",
    "message_notify_user": lambda args: "Sending notification to user",
    "message_ask_user": lambda args: "Asking user for input",
    "message_email_user": lambda args: f"Sending email to {args.get('recipient')}",
    "info_search_web": lambda args: f"Searching web for: {args.get('query')}",
}

###############################################################################
# Agent Management Tools                                                     #
###############################################################################


class Phase(BaseModel):
    id: int
    title: str
    required_capabilities: str


@function_tool
def agent_update_plan(
    *,
    current_phase_id: Optional[int] = None,
    goal: Optional[str] = None,
    phases: Optional[List[Phase]] = None,
) -> None:
    """Create or update the task plan.

    When to use:
    - When there is no task plan yet. In this case, the current_phase_id should be 1.
    - When user makes a new request or asks a follow-up
    - When new information discovered makes the current plan obsolete
    - When the capabilities required have changed significantly
    - When the current plan is inefficient or fails repeatedly

    Best practices:
    - Break down the goal into phases based on required capabilities to enable phase-wise optimization
    - Each phase can involve multiple related capabilities, but avoid overloading; prefer splitting into smaller phases
    - Aim for a detailed breakdown: simple tasks ≈2 phases, typical 4–6, complex 10+
    - Phases should be high-level units of work, not implementation details
    - MUST examine candidate `required_capabilities` carefully, DO NOT miss any necessary capabilities
    - If a phase only involves basic LLM capabilities (e.g. chatting, summarizing, translating), leave `required_capabilities` empty
    - Make delivering results to the user a separate phase, typically the final phase
    - Actively update the task plan when significant new information emerges (e.g. a need for deeper investigation)

    """
    if current_phase_id is not None:
        _agent_state["current_phase_id"] = current_phase_id

    if goal is not None:
        _agent_state["goal"] = goal
    if phases is not None:
        _agent_state["phases"] = phases

    print(
        f"Task plan updated:\n<task_plan>\nGoal:\n{_agent_state['goal']}\n\nCurrent phase:\n{_agent_state['current_phase_id']}\n</task_plan>\n"
    )

    return {
        "response": f"Task plan updated:\n<task_plan>\nGoal:\n{_agent_state['goal']}\n\nPhases:\n{_agent_state['phases']}\n\nCurrent phase:\n{_agent_state['current_phase_id']}\n</task_plan>\n"
    }


@function_tool
def agent_advance_phase(*, from_phase_id: int, to_phase_id: int) -> None:
    """Advance to the next phase in the task plan.

    When to use:
    - When the current phase is complete and the next phase is ready to start

    Best practices:
    - After completing a phase, MUST use this tool before executing specific operations for the next phase
    - Don't rush to completion; each phase may require multiple iterations before completion, only advance when confident enough
    - `to_phase_id` MUST be the next sequential ID after `from_phase_id`, skipping phases or going backward is NOT allowed
    - If skipping phases or going backward is needed, it indicates the task plan needs updating, and MUST use the `agent_update_plan` tool
    """
    if _agent_state["current_phase_id"] != from_phase_id:
        raise ValueError(
            f"Cannot advance: agent is in phase {_agent_state['current_phase_id']}, not {from_phase_id}."
        )
    _agent_state["current_phase_id"] = to_phase_id
    print(f"[Agent] Advanced from phase {from_phase_id} ➡ {to_phase_id}")
    return {
        "response": f"Advanced to the next phase:\n<task_plan>\nGoal:\n{_agent_state['goal']}\n\nPhases:\n{_agent_state['phases']}\n\nPrevious phase: {_agent_state['current_phase_id']}\n\nNext phase: {to_phase_id}\n</task_plan>\n<best_practices>\n[Relevant best practices for the new phase]\n</best_practices>\n<related_knowledge>\n[Relevant knowledge for the new phase]\n</related_knowledge>"
    }


@function_tool
def agent_end_task() -> None:
    """End the task and wait for new instructions.

    When to use:
    - When all phases in the task plan are completed and results are delivered to the user through message tools
    - When user explicitly requests to stop

    Best practices:
    - MUST use this tool as the final action in the agent loop
    - MUST use this tool to stop immediately when user explicitly requests to stop
    - DO NOT use this tool when failed to complete a task; instead, use the `message_ask_user` tool to ask for guidance
    - DO NOT use this tool when the user changes task or presents new requirement; instead, update the task plan directly
    """
    _agent_state["completed"] = True
    print("[Agent] Task marked as completed.")
    return {"response": "ok"}


@function_tool
def agent_schedule_task(
    *,
    task_description: str,
    schedule_type: str,
    start_time: str,
) -> None:
    """Schedule a task for future execution.

    Currently supports basic scheduling metadata storage; integrate with your
    preferred scheduler (e.g. cron, APScheduler) for real use‑cases.
    """
    try:
        start_dt = datetime.fromisoformat(start_time)
    except ValueError as exc:
        raise ValueError(
            "start_time must be in ISO format, e.g. '2025-06-18 09:00:00'"
        ) from exc

    _agent_state["scheduled_tasks"].append(
        {
            "task_description": task_description,
            "schedule_type": schedule_type,
            "start_time": start_dt,
        }
    )
    print(
        f"[Agent] Scheduled task '{task_description}' ({schedule_type}) starting at {start_dt}."
    )


###############################################################################
# Message Tools (stubs — integrate with your messaging infra)                #
###############################################################################


@function_tool
def message_notify_user(*, text: str, attachments: Optional[List[str]] = None) -> dict:
    """Send a message to the user.

    When to use:
    - When a user message is received
    - When achieving milestone progress or significant changes in task planning
    - When attachments need to be shown to user
    - When the task is completed and results are ready to be delivered
    - When user asks a follow-up question after a task is completed

    Best practices:
    - Use this tool for user communication instead of direct text output
    - MUST reply to user messages immediately before planning or taking any other actions
    - DO NOT provide direct answers without prior analysis, even for simple requests
    - During ongoing tasks, respond promptly to acknowledge user interruptions or updates
    - Files in attachments MUST use absolute paths within the sandbox
    - Messages MUST be informative (no need for user response), avoid questions
    - Avoid using emoji unless absolutely necessary
    - MUST provide all relevant files as attachments since user may not have direct access to local filesystem
    - When reporting task completion, include important deliverables or URLs as attachments
    - When providing multiple attachments, MUST arrange by descending order of importance or relevance
    - Before ending the task, MUST use this tool to deliver results to the user"""
    print(f"[Notify] {text}")
    if attachments:
        print(f"[Notify] Attachments: {attachments}")
    return {"message_notify_user_response": {"response": "Message sent to user"}}


@function_tool
def message_ask_user(
    *,
    text: str,
    attachments: Optional[List[str]] = None,
    options: Optional[List[str]] = None,
) -> str:
    """Ask the user a question and wait for response.

    When to use:
    - When user presents ambiguous or unclear requirements
    - When user input or guidance is absolutely necessary to proceed with the task
    - When confirmation is needed before performing sensitive browser operations
    - When suggesting user to take over browser to complete operations
    - When upgrading subscription is required to unlock a feature

    Best practices:
    - Use this tool to request user responses instead of direct text output
    - Request user responses only when necessary to minimize user disruption and avoid blocking progress
    - Questions MUST be clear and unambiguous; if options exist, clearly list all available choices
    - Avoid using emoji unless absolutely necessary
    - MUST provide all relevant files as attachments since user may not have direct access to local filesystem
    - MUST use `confirm_browser_operation` in `suggested_user_action` before sensitive browser operations (e.g., posting content, completing payment)
    - Use `take_over_browser` in `suggested_user_action` when user takeover is required (e.g., login, providing personal information)
    - MUST open the corresponding webpage before suggesting user takeover
    - When suggesting takeover, also indicate that the user can choose to provide necessary information via messages
    - Use `upgrade_to_unlock_feature` in `suggested_user_action` when the user needs to upgrade subscription to unlock a feature
    - When suggesting upgrade, MUST also provide alternative options if available, such as using a different tool or approach
    """
    prompt = f"[Ask] {text}\n"
    if attachments:
        print(f"[Ask] Attachments: {attachments}")
    if options:
        if not options:
            raise ValueError("Options list must be non-empty if provided")
        prompt += " / ".join(options) + "\n> "
    else:
        prompt += "> "
    return input(prompt)


@function_tool
def message_email_user(*, recipient: str, subject: str, body: str) -> None:
    """Send an email to the recipient.

    This is a minimal SMTP example; configure host/port/auth as needed.
    """
    msg = EmailMessage()
    msg["To"] = recipient
    msg["From"] = os.getenv("EMAIL_FROM", "noreply@example.com")
    msg["Subject"] = subject
    msg.set_content(body)

    try:
        smtp_host = os.getenv("EMAIL_SMTP_HOST", "localhost")
        smtp_port = int(os.getenv("EMAIL_SMTP_PORT", "25"))
        with smtplib.SMTP(smtp_host, smtp_port) as smtp:
            smtp.send_message(msg)
        print(f"[Email] Sent to {recipient}: {subject}")
    except Exception as exc:
        print(f"[Email] Failed to send: {exc}")


###############################################################################
# File System Tools                                                          #
###############################################################################

# Helper


def _resolve(path: str | Path) -> Path:
    """Return an absolute, expanded *Path* object for **path**."""
    return Path(os.path.expanduser(path)).resolve()


@function_tool
def file_read(
    *,
    file: str,
    start_line: Optional[int] = None,
    end_line: Optional[int] = None,
    sudo: bool = False,
) -> str:
    """Read the content of a text file.

    When to use:
    - When reading content of a text file

    Best practices:
    - This tool supports text-based or line-oriented formats only
    - Use line range limits appropriately; when uncertain, start by reading first 20 lines
    - Be mindful of performance impact with large files
    """
    p = _resolve(file)

    if not p.exists():
        raise FileNotFoundError(f"File not found: {file}")

    content = p.read_text()

    if start_line is not None or end_line is not None:
        lines = content.splitlines()
        start = start_line if start_line is not None else 0
        end = end_line if end_line is not None else len(lines)

        if start < 0 or end > len(lines) or start >= end:
            raise ValueError(
                f"Invalid line range: start_line={start_line}, end_line={end_line}, file has {len(lines)} lines"
            )

        content = "\n".join(lines[start:end])

    return content


@function_tool
def file_write(*, path: str, content: str) -> None:
    """Overwrite the content of a text file.

    When to use:
    - When you need to create a new file
    - When you need to overwrite an existing file with new content

    Best practices:
    - Strictly follow requirements in <writing_guidelines> and other best practices
    - Avoid using list formats in any files except todo.md
    - DO NOT output snipped or truncated content, always output full content"""
    p = _resolve(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content)
    return {"response": f"File written: {path}"}


@function_tool
def file_append_text(*, path: str, content: str) -> None:
    """Append content to a text file.

    When to use:
    - When you need to add new content to an existing file without overwriting it

    Best practices:
    - Strictly follow requirements in <writing_guidelines> and other best practices
    - Avoid using list formats in any files except todo.md
    - DO NOT output snipped or truncated content, always output full content
    """
    p = _resolve(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("a", encoding="utf-8") as fh:
        fh.write(content)
    return {"response": f"File appended: {path}"}


@function_tool
def file_replace_text(*, path: str, old_text: str, new_text: str) -> None:
    """Replace specified string in a text file.

    When to use:
    - When updating specific content in files
    - When fixing errors in code files
    - When updating markers in todo.md

    Best practices:
    - The `old_str` parameter MUST exactly match one or more consecutive lines in the source file
    - If `old_text` appears multiple times in the source file, an error will be raised
    """
    p = _resolve(path)
    content = p.read_text()
    if content.count(old_text) > 1:
        raise ValueError(
            f"Error: '{old_text}' appears multiple times in the file. Please provide a more specific old_text to avoid ambiguity."
        )
    p.write_text(content.replace(old_text, new_text))
    return {
        "response": f"File edited: {path}, Latest content with line numbers: {new_text}"
    }


@function_tool
def file_delete(*, path: str) -> None:
    """Delete the file at *path*."""
    p = _resolve(path)
    if p.is_dir():
        shutil.rmtree(p)
    else:
        p.unlink(missing_ok=True)
    return {"response": f"File deleted: {path}"}


@function_tool
def file_list(*, path: str) -> List[str]:
    """Return a list of files/directories in *path*."""
    p = _resolve(path)
    return [str(child) for child in p.iterdir()]


@function_tool
def file_make_dir(*, path: str) -> None:
    """Create a directory (and parents) at *path*."""
    _resolve(path).mkdir(parents=True, exist_ok=True)
    return {"response": f"Directory created: {path}"}


@function_tool
def file_copy(*, source: str, destination: str) -> None:
    """Copy *source* to *destination* (file or directory)."""
    src, dst = _resolve(source), _resolve(destination)
    if src.is_dir():
        shutil.copytree(src, dst, dirs_exist_ok=True)
    else:
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
    return {"response": f"File copied: {source} to {destination}"}


@function_tool
def file_move(*, source: str, destination: str) -> None:
    """Move *source* to *destination* (file or directory)."""
    src, dst = _resolve(source), _resolve(destination)
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(src, dst)
    return {"response": f"File moved: {source} to {destination}"}


###############################################################################
# End of module                                                              #
###############################################################################


def get_tool_description(tool_name: str, args: dict) -> str:
    """
    Get a user-friendly description of a tool operation based on its arguments.

    Args:
        tool_name: The name of the tool being called
        args: Dictionary of arguments passed to the tool

    Returns:
        A formatted string describing what the tool is doing
    """
    if tool_name in tool_description_map:
        return tool_description_map[tool_name](args)
    return f"Using tool: {tool_name}"


@function_tool
def info_search_web(query: str, date_range: str = "all", num: int = 5) -> dict:
    """
    Search web pages using Google Custom Search API.

    Args:
        query (str): Search query in Google search style, using 3-5 keywords.
        date_range (str): Optional time filter ('all', 'past_hour', 'past_day', 'past_week', 'past_month', 'past_year').
        num (int): Number of results to return (default 5).

    Returns:
        dict: The search results from Google Custom Search API.
    """

    api_key = os.getenv("GOOGLE_API_KEY", "Your Google API Key")
    cx = os.getenv("GOOGLE_SEARCH_CX", "")
    url = "https://www.googleapis.com/customsearch/v1"

    params = {"q": query, "num": num, "key": api_key, "cx": cx}

    # Add time filter if applicable
    if date_range != "all":
        date_restrict_map = {
            "past_hour": "h1",
            "past_day": "d1",
            "past_week": "w1",
            "past_month": "m1",
            "past_year": "y1",
        }
        if date_range in date_restrict_map:
            params["dateRestrict"] = date_restrict_map[date_range]

    response = requests.get(url, params=params)

    if response.status_code != 200:
        raise Exception(
            f"Google Custom Search API error: {response.status_code}, {response.text}"
        )

    return response.json()
