"""Tool for generating and writing code."""
from typing import Any, List, Union

from steamship import Block, Task
from steamship.agents.schema import AgentContext
from steamship.agents.schema.tool import Tool


class CodeGenerationTool(Tool):
    """Tool to generate and write code based on natural language descriptions.
    
    This tool allows the companion to write, generate, and refactor code based on
    user requests. It's designed for intimate companion use in engineering workflows.
    """

    name: str = "CodeGenerationTool"
    human_description: str = (
        "Generate, write, or refactor code. Provide a description of what code "
        "you need written, including programming language, requirements, and any "
        "specific patterns or libraries you want used."
    )
    agent_description: str = (
        "Generate code based on user requirements. Always provide complete, "
        "working code with proper error handling, type hints, and documentation."
    )

    def run(
        self, tool_input: List[Block], context: AgentContext, **kwargs
    ) -> Union[List[Block], Task[Any]]:
        """Generate code based on input description."""
        if not tool_input or not tool_input[0].text:
            return [Block(text="Please provide a code generation request.")]

        prompt = tool_input[0].text
        
        # Create a code generation prompt for the LLM
        code_prompt = f"""You are an expert code generation assistant for an intimate engineering companion.

User request: {prompt}

Generate complete, production-ready code that:
1. Is well-documented with docstrings and comments
2. Includes proper error handling and logging
3. Uses type hints for Python code
4. Follows best practices and design patterns
5. Is tested and ready to use

Format the code in a clear code block with the language specified.
Include any necessary imports and dependencies.
If multiple files are needed, clearly separate them.
"""
        
        # Return the prompt for the agent's LLM to process
        # The agent will use its configured LLM to generate the actual code
        return [Block(text=f"Code Request:\n{code_prompt}")]


class CodeRefactoringTool(Tool):
    """Tool to refactor and optimize existing code."""

    name: str = "CodeRefactoringTool"
    human_description: str = (
        "Refactor or optimize existing code. Provide the current code and describe "
        "what improvements you want (performance, readability, patterns, etc.)"
    )
    agent_description: str = (
        "Refactor code for better performance, readability, or to apply design patterns."
    )

    def run(
        self, tool_input: List[Block], context: AgentContext, **kwargs
    ) -> Union[List[Block], Task[Any]]:
        """Refactor code based on input."""
        if not tool_input or not tool_input[0].text:
            return [Block(text="Please provide code to refactor.")]

        code_content = tool_input[0].text
        
        refactor_prompt = f"""You are an expert code refactoring assistant.

Current code:
{code_content}

Guidelines:
1. Improve readability and maintainability
2. Apply appropriate design patterns
3. Optimize performance where applicable
4. Maintain the original functionality
5. Add or improve type hints
6. Enhance error handling

Provide the refactored code with explanations of changes made."""
        
        return [Block(text=f"Refactoring Request:\n{refactor_prompt}")]
