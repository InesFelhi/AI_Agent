import pytest

from src.prompts.prompt import (
    build_workflow_generation_prompt,
    build_job_question_prompt,
)


def test_workflow_generation_prompt_contains_context_instruction():
    context = "Workflow app automation for network checks"
    instruction = "Generate a command stage workflow to ping 8.8.8.8 and capture output."
    examples = """Example:
Start -1000
CmdStage -1001 ping -c 1 8.8.8.8
End -2000"""

    system_prompt, user_prompt = build_workflow_generation_prompt(context, instruction, task_examples=examples)

    # Check both system and user prompts contain key content
    full_prompt = system_prompt + " " + user_prompt
    assert "Start" in full_prompt or context in full_prompt
    assert context in full_prompt
    assert instruction in user_prompt

    # Debug output
    print("=== System Prompt ===")
    print(system_prompt)
    print("=== User Prompt ===")
    print(user_prompt)


def test_job_question_prompt_is_qa_style():
    context = "Job X is running on device Y"
    question = "What is the current status of the job?"

    prompt = build_job_question_prompt(context, question)

    assert "job assistant" in prompt
    assert context in prompt
    assert question in prompt

    print("=== Job Question Prompt ===")
    print(prompt)
