# Virtual Environment Setup Instructions

## Virtual Environment Created ✓

A Python virtual environment has been created in the `venv` folder.

## Activation Instructions

### Windows (PowerShell)
```powershell
.\venv\Scripts\Activate.ps1
```

### Windows (Command Prompt)
```cmd
venv\Scripts\activate
```

### Windows (Git Bash)
```bash
source venv/Scripts/activate
```

## Install Dependencies

After activating the virtual environment, install the required packages:

```bash
pip install -r requirements.txt
```

## Verify Installation

Check that packages are installed:

```bash
pip list
```

You should see:
- langgraph
- langchain
- langchain-openai
- langchain-community
- gradio
- python-dotenv
- pydantic

## Run the Application

Once dependencies are installed:

```bash
python sql_processor_app.py
```

## Deactivate

When you're done, deactivate the virtual environment:

```bash
deactivate
```

## Troubleshooting

If you get an execution policy error in PowerShell, run:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

Then try activating again.

