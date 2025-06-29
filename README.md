# Super AI Agent

A powerful autonomous agent framework capable of breaking down complex tasks into manageable phases and executing them with minimal human intervention.

## 🌟 Overview

Super AI Agent is an advanced autonomous agent system built on top of OpenAI's Agent framework. It excels at handling multi-step, complex tasks by implementing a structured workflow that includes strategic planning, iterative execution, and comprehensive documentation.

## ✨ Key Features

- **Strategic Planning**: Automatically breaks down complex tasks into well-defined phases
- **Autonomous Execution**: Completes tasks with minimal human intervention
- **Dynamic Phase Management**: Advances through task phases as work progresses
- **Comprehensive Documentation**: Creates detailed reports and maintains task tracking
- **Web Search Integration**: Gathers up-to-date information from the web
- **File System Operations**: Manages files and directories as needed for task completion
- **User Communication**: Notifies users of progress and requests input when necessary

## 🚀 What Makes Super AI Agent Superior

Unlike other agent frameworks that require extensive prompting or lack structure, Super AI Agent:

1. **Implements a Structured Workflow**: Follows a clear, methodical approach to problem-solving
2. **Maintains Task State**: Keeps track of progress across phases and steps
3. **Creates Comprehensive Documentation**: Generates detailed reports with proper citations
4. **Prioritizes Up-to-Date Information**: Uses web search rather than relying on potentially outdated knowledge
5. **Manages Its Own Workflow**: Creates and updates todo lists to track progress
6. **Handles Complex, Multi-Phase Tasks**: Excels at projects requiring multiple capabilities and steps

## 🛠️ Available Tools & Workflow

Super AI Agent leverages a comprehensive set of tools to accomplish tasks autonomously:

### Agent Management Tools
- **agent_update_plan**: Creates or updates the task plan with goals and phases
- **agent_advance_phase**: Advances to the next phase when current phase is complete
- **agent_end_task**: Concludes the task when all objectives are met
- **agent_schedule_task**: Schedules tasks for future execution

### Communication Tools
- **message_notify_user**: Sends updates and notifications to the user
- **message_ask_user**: Requests input or clarification from the user
- **message_email_user**: Sends email communications when needed

### File System Tools
- **file_read**: Reads file contents, with options for specific line ranges
- **file_write**: Creates new files or overwrites existing ones
- **file_append_text**: Adds content to existing files
- **file_replace_text**: Updates specific text within files
- **file_delete**: Removes files when no longer needed
- **file_list**: Lists contents of directories
- **file_make_dir**: Creates new directories
- **file_copy/file_move**: Manages file organization

### Information Tools
- **info_search_web**: Searches the web for up-to-date information

### Workflow Process
1. **Strategic Planning**: Upon receiving a task, the agent analyzes requirements and formulates a goal with sequential phases
2. **Task Tracking**: Creates and maintains a `todo.md` file to track progress
3. **Iterative Execution**: For each step in the current phase:
   - Conducts deep research on the task
   - Documents findings in dedicated files
   - Uses web search to gather current data
   - Marks steps as completed and advances when appropriate
4. **Documentation**: Creates comprehensive reports with proper citations
5. **Communication**: Keeps the user informed throughout the process
6. **Delivery**: Provides final deliverables and concludes the task

## 🛠️ Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/super-ai-agent.git
cd super-ai-agent

# Create a virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

## ⚙️ Configuration

1. Copy the sample environment file to create your own:
   ```bash
   cp .env.sample .env
   ```

2. Edit the `.env` file and configure the following variables:

   ### Required Environment Variables
   - `OPENAI_API_KEY`: Your OpenAI API key (required for the agent to function)

   ### Optional Environment Variables
   - **Email Configuration** (for email_user tool)
     - `EMAIL_FROM`: Sender email address (default: noreply@example.com)
     - `EMAIL_SMTP_HOST`: SMTP server hostname (default: localhost)
     - `EMAIL_SMTP_PORT`: SMTP server port (default: 25)

   - **Web Search Configuration** (for info_search_web tool)
     - `GOOGLE_API_KEY`: Your Google API key for web searches
     - `GOOGLE_SEARCH_CX`: Your Google Custom Search Engine ID

Example `.env` file:
```
# OpenAI API Key (Required)
OPENAI_API_KEY=your_openai_api_key_here

# Email Configuration (Optional)
EMAIL_FROM=noreply@example.com
EMAIL_SMTP_HOST=localhost
EMAIL_SMTP_PORT=25

# Google Search Configuration (Optional)
GOOGLE_API_KEY=your_google_api_key_here
GOOGLE_SEARCH_CX=your_google_search_cx_here
```

## 🚀 Usage

Run the agent with:

```bash
python run.py
```

You can modify the initial user query in `run.py` to start the agent with a different task:

```python
messages = [
    {
        "role": "user",
        "content": "Your task description here",
    }
]
```

## 📋 Example Tasks

Super AI Agent can handle a wide range of tasks, including:

- Research and report writing
- Data analysis and visualization
- Content creation and curation
- Project planning and management
- Information gathering and synthesis

## 🧩 Project Structure

- `run.py`: Main entry point for running the agent
- `tools.py`: Implementation of all agent tools (file operations, web search, etc.)
- `prompt.txt`: System instructions that define the agent's workflow
- `requirements.txt`: Project dependencies
- `.env.sample`: Sample environment variables configuration

## 📄 License

MIT

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request. 