from __future__ import annotations
import asyncio
import os
from openai import AsyncOpenAI
from agents import (
    Agent,
    Runner,
    ModelSettings,
    OpenAIResponsesModel,
    AgentHooks,
    Tool,
    RunContextWrapper,
)
from agents import ItemHelpers
from pathlib import Path
from tools import (
    agent_update_plan,
    agent_advance_phase,
    agent_end_task,
    agent_schedule_task,
    message_notify_user,
    message_ask_user,
    message_email_user,
    file_read,
    file_write,
    file_append_text,
    file_replace_text,
    file_delete,
    file_list,
    file_make_dir,
    file_copy,
    file_move,
    info_search_web,
    _agent_state,
    get_tool_description,
)
import json
from dotenv import load_dotenv

load_dotenv()

prompt_file = Path(__file__).parent / "prompt.txt"
PROMPT = prompt_file.read_text()


class StepPromptHook(AgentHooks):
    """
    Keeps the original prompt intact and idempotent.
    """

    def __init__(self):
        self.current_phase_id: int | None = None

    async def on_tool_end(
        self, context: RunContextWrapper, agent: Agent, tool: Tool, result: str
    ) -> None:
        phase_id = _agent_state["current_phase_id"]

        if self.current_phase_id == phase_id:
            return

        # Remove previous phase instruction if exists
        if phase_id > 1:
            last_phase = f"You are in phase {phase_id-1}, with the goal of {_agent_state['goal']} and the current phase is {_agent_state['phases'][phase_id-2]}. If this is empty, then create a plan first. If it is not empty, then continue with the current phase, and consider this as your main task."
            if last_phase in agent.instructions:
                agent.instructions = agent.instructions.replace(last_phase, "")

        # Add current phase instruction
        self.current_phase_id = phase_id
        current_phase = f"You are in phase {phase_id}, with the goal of {_agent_state['goal']} and the current phase is {_agent_state['phases'][phase_id-1]}. If this is empty, then create a plan first. If it is not empty, then continue with the current phase, and consider this as your main task."
        agent.instructions = agent.instructions + "\n\n" + current_phase
        # print(f"Updated prompt: {agent.instructions}")


def build_agent(client: AsyncOpenAI) -> Agent:
    # The Code Interpreter tool definition provided by the SDK.
    model_cfg = OpenAIResponsesModel(model="gpt-4.1", openai_client=client)

    agent = Agent(
        name="DevAssistant",
        instructions=(PROMPT),
        model=model_cfg,
        tools=[
            agent_update_plan,
            agent_advance_phase,
            agent_end_task,
            agent_schedule_task,
            message_notify_user,
            message_ask_user,
            message_email_user,
            file_read,
            file_write,
            file_append_text,
            file_replace_text,
            file_delete,
            file_list,
            file_make_dir,
            file_copy,
            file_move,
            info_search_web,
        ],
        model_settings=ModelSettings(parallel_tool_calls=True),
        hooks=StepPromptHook(),
    )

    return agent


async def run_demo() -> None:
    """Run a sample conversation and stream every event to the console."""

    api_key = os.getenv("OPENAI_API_KEY", "")
    if not api_key or api_key == "YOUR_API_KEY_HERE":
        raise RuntimeError(
            "🔑  Please set the OPENAI_API_KEY environment variable before running."
        )

    client = AsyncOpenAI(api_key=api_key)
    agent = build_agent(client)

    # A single‑turn conversation asking the assistant to run some code.
    messages = [
        {
            "role": "user",
            "content": "Research the latest news on the stock market and write a report on it",
        }
    ]

    stream = Runner.run_streamed(agent, messages, max_turns=70)

    async for event in stream.stream_events():
        # ── Handle agent switches (useful if you have multiple agents) ──────────
        if event.type == "agent_updated_stream_event":
            print(f"\n── Switched to agent: {event.new_agent.name} ──\n")
            continue

        # ── Handle the granular run‑item events ────────────────────────────────
        if event.type == "run_item_stream_event":
            item = event.item

            # Tool call started — print the code / arguments being sent.
            if item.type == "tool_call_item":
                raw = (
                    item.raw_item
                )  # ResponseFunctionToolCall or ResponseCodeInterpreterToolCall

                if raw.type == "code_interpreter_call":
                    print("====Code Interpreter Call=====")
                    print(raw.code)
                    print("====End of Code Interpreter Call=====")
                else:
                    if raw.name == "agent_end_task":
                        print("====End of Task=====")
                        break

                    # Use the tool_description_map to get a cleaner log message
                    try:
                        args = json.loads(getattr(raw, "arguments", "{}"))
                        description = get_tool_description(raw.name, args)
                        print(f"[Tool Call] {description}")
                    except Exception:
                        # Fallback to original behavior if there's an error
                        print(f"[Tool Call] {raw.name}")
                        print(f"Arguments: {getattr(raw, 'arguments', '{}')}")

            # Tool produced its output — e.g. stdout, images, etc.
            # elif item.type == "tool_call_output_item":
            #     print("[Tool Output]")
            #     print(item.output)
            #     print()

            # Assistant sent (part of) a normal message.
            elif item.type == "message_output_item":
                msg_text = ItemHelpers.text_message_output(item)
                print("[Assistant]", msg_text)


if __name__ == "__main__":
    asyncio.run(run_demo())
