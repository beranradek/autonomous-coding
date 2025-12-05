"""
Prompt Loading Utilities
========================

Functions for loading prompt templates from the prompts directory.
"""

import shutil
from pathlib import Path


PROMPTS_DIR = Path(__file__).parent / "prompts"


def load_prompt(name: str) -> str:
    """Load a prompt template from the prompts directory."""
    prompt_path = PROMPTS_DIR / f"{name}.md"
    return prompt_path.read_text()


def get_initializer_prompt() -> str:
    """Load the initializer prompt."""
    return load_prompt("initializer_prompt")


def get_coding_prompt() -> str:
    """Load the coding agent prompt."""
    return load_prompt("coding_prompt")


def get_enhancement_initializer_prompt() -> str:
    """Load the enhancement initializer prompt for existing projects."""
    return load_prompt("enhancement_initializer_prompt")


def copy_spec_to_project(project_dir: Path) -> None:
    """Copy the app spec file into the project directory for the agent to read."""
    spec_source = PROMPTS_DIR / "app_spec.txt"
    spec_dest = project_dir / "app_spec.txt"
    if not spec_dest.exists():
        shutil.copy(spec_source, spec_dest)
        print("Copied app_spec.txt to project directory")


def copy_or_verify_spec(project_dir: Path) -> None:
    """Copy spec if missing, or verify it exists for existing projects."""
    spec_dest = project_dir / "app_spec.txt"
    if spec_dest.exists():
        print("Using existing app_spec.txt in project directory")
    else:
        spec_source = PROMPTS_DIR / "app_spec.txt"
        if spec_source.exists():
            shutil.copy(spec_source, spec_dest)
            print("Copied app_spec.txt to project directory")
        else:
            raise FileNotFoundError(
                "No app_spec.txt found. Please create one in the project directory "
                "describing the features you want to add."
            )
