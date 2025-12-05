# Generating app_spec.txt Files

This guide explains how to create `app_spec.txt` files for the autonomous coding agent.

## Quick Start

### Option 1: Use the App Spec Generator Prompt

Use an AI assistant with the generator prompt to create your specification:

```bash
# In Claude or another AI assistant, use this prompt:
cat prompts/app_spec_generator_prompt.md

# Then describe what you want to build
```

The AI will ask clarifying questions and generate a complete `app_spec.txt` for you.

### Option 2: Start from Example

Copy and modify the example:

```bash
# Copy the example
cp prompts/app_spec_example.txt prompts/app_spec.txt

# Edit it for your needs
nano prompts/app_spec.txt
```

## What to Include in Your Requirements

### For New Projects (Greenfield)

Provide:
- **What you're building**: "A task management app like Todoist"
- **Technology preferences**: "React frontend, Node.js backend"
- **Feature scope**: "About 50 features" or "Comprehensive with 200+ features"
- **Key functionality**: "Projects, tags, priorities, recurring tasks"
- **Design style**: "Clean, minimal UI similar to Todoist"

### For Existing Projects (Enhancement Mode)

Provide:
- **Current state**: "I have an e-commerce site built with Django"
- **What to add**: "Add a sales analytics dashboard"
- **Feature count**: "Generate 30 new features"
- **Integration needs**: "Should use existing user authentication"
- **Technology constraints**: "Must use PostgreSQL like the rest of the app"

## Feature Count Guidelines

The number of features determines how comprehensive the specification should be:

| Feature Count | Scope | Example Use Case |
|---------------|-------|------------------|
| 10-20 | Small addition | Add a simple feature to existing app |
| 30-50 | Medium project | Build a focused tool or add substantial features |
| 100-150 | Large project | Build a complete application |
| 200+ | Comprehensive | Build a feature-rich platform like the Claude.ai example |

**Important:** Be specific about feature count in your requirements!
- ❌ "Add analytics" (vague)
- ✅ "Add analytics dashboard with 25 features" (specific)

## Example Requests

### Example 1: Greenfield Project
```
I want to build a personal finance tracker web app.

Technology:
- React with TypeScript frontend
- Node.js + Express backend
- PostgreSQL database
- Tailwind CSS for styling

Features (generate ~100 features):
- Account management (multiple bank accounts, credit cards)
- Transaction tracking with categories
- Budget creation and tracking
- Bill reminders
- Financial reports and charts
- Export to CSV/PDF
- Mobile responsive design

Design: Clean, modern, similar to Mint.com
```

### Example 2: Enhancement to Existing Project
```
I have an existing blog platform built with Next.js and MongoDB.

Add the following new features (generate 40 test cases):
- Comment system with threading
- User profiles with avatars
- Social sharing (Twitter, Facebook, LinkedIn)
- Related posts recommendations
- Email newsletter signup
- Reading time estimates
- Dark mode toggle
- Table of contents for long posts

Match the existing Next.js/MongoDB stack.
```

### Example 3: Reference Example
```
Build a chat application similar to the Claude.ai clone example, but:
- Use Python FastAPI instead of Node.js
- Use PostgreSQL instead of SQLite
- Add voice message support
- Add file sharing in conversations
- Target 150 features (smaller scope than the 200 in the example)
```

## Using the Generated Specification

Once you have your `app_spec.txt`:

### For Greenfield Projects
```bash
# Place it in the prompts directory
cp app_spec.txt prompts/app_spec.txt

# Run the agent
python autonomous_agent.py --project-dir ./my_new_project
```

### For Enhancement Projects
```bash
# Place it in your existing project directory
cp app_spec.txt /path/to/existing/project/app_spec.txt

# Run the agent
python autonomous_agent.py --project-dir /path/to/existing/project --mode enhancement
```

## Tips for Good Specifications

1. **Be specific about technology**: "React 18 with Vite" not just "React"
2. **Include design preferences**: Reference existing apps for style guidance
3. **Specify feature count explicitly**: This helps scope the project
4. **List must-have vs nice-to-have**: Prioritize features
5. **Include success criteria**: Define what "done" means
6. **For enhancements**: Clearly state what already exists

## Quality Checklist

Before using your `app_spec.txt`, verify:

- ✅ Technology stack is clearly specified
- ✅ All major feature areas are covered
- ✅ Database schema is outlined (if applicable)
- ✅ UI/UX approach is described
- ✅ Feature count matches your needs
- ✅ Implementation steps are logical
- ✅ Success criteria are defined
