import gradio as gr
from sql_processor import SQLProcessor


async def setup():
    """
    Initialize SQL processor for Gradio interface.
    
    Creates a new SQLProcessor instance and sets it up with LLMs and tools.
    Called when the Gradio interface loads.
    
    Returns:
        Initialized SQLProcessor instance
    """
    processor = SQLProcessor()
    await processor.setup()
    return processor


async def process_message(processor, message, success_criteria, history):
    """
    Process a user message through the SQL processor workflow.
    
    This function:
    1. Normalizes conversation history format
    2. Runs the processor workflow with user message
    3. Formats results for Gradio Chatbot component
    4. Returns updated conversation history
    
    Args:
        processor: SQLProcessor instance
        message: User's input message
        success_criteria: Optional success criteria
        history: Previous conversation history
        
    Returns:
        Tuple of (formatted_results, processor) where formatted_results is
        a list of message dicts with 'role' and 'content' keys for Gradio
    """
    # Convert history to list if None
    if history is None:
        history = []
    
    # Ensure history is in correct format (list of dicts with role/content)
    normalized_history = []
    for msg in history:
        if isinstance(msg, dict) and "role" in msg and "content" in msg:
            normalized_history.append(msg)
        elif isinstance(msg, tuple) and len(msg) == 2:
            # Convert tuple (user_msg, bot_msg) to dict format
            user_msg, bot_msg = msg
            if user_msg:
                normalized_history.append({"role": "user", "content": user_msg})
            if bot_msg:
                normalized_history.append({"role": "assistant", "content": bot_msg})
    
    results = await processor.run_superstep(message, success_criteria, normalized_history)
    
    # Ensure all messages are in the correct format for Gradio Chatbot
    # Gradio expects: list of dicts with 'role' and 'content' keys
    formatted_results = []
    
    for msg in results:
        if isinstance(msg, dict):
            # Ensure it has the required keys
            if "role" in msg and "content" in msg:
                formatted_results.append({
                    "role": msg["role"],
                    "content": str(msg["content"]) if msg["content"] is not None else ""
                })
        elif isinstance(msg, tuple):
            # Convert tuple format (user_msg, bot_msg) to dict format
            if len(msg) == 2:
                user_msg, bot_msg = msg
                if user_msg:
                    formatted_results.append({"role": "user", "content": str(user_msg)})
                if bot_msg:
                    formatted_results.append({"role": "assistant", "content": str(bot_msg)})
        else:
            # Handle string or other formats
            formatted_results.append({"role": "assistant", "content": str(msg)})
    
    return formatted_results, processor


async def reset():
    """
    Reset the SQL processor and clear conversation.
    
    Creates a new SQLProcessor instance and clears the UI inputs.
    Called when user clicks the Reset button.
    
    Returns:
        Tuple of empty strings and None values to clear UI components, plus new processor
    """
    new_processor = SQLProcessor()
    await new_processor.setup()
    return "", "", None, new_processor


def free_resources(processor):
    """
    Cleanup function called when processor state is deleted.
    
    Ensures proper cleanup of resources when the Gradio interface
    is closed or processor is reset. Called automatically by Gradio's
    State component delete_callback.
    
    Args:
        processor: SQLProcessor instance to clean up
    """
    print("Cleaning up")
    try:
        if processor:
            processor.cleanup()
    except Exception as e:
        print(f"Exception during cleanup: {e}")


with gr.Blocks(title="SQL Processor") as ui:
    gr.Markdown("## SQL Processor - Banking Data Warehouse")
    gr.Markdown("""
    This tool processes SQL files for banking data warehouses:
    - Reads SQL files from relative or absolute paths
    - Applies banking nomenclature conventions
    - Generates separate DDL and DML files
    - Adds banking controls and audit comments
    - Ensures files are ready for execution and audit
    - Verifies Snowflake compliance (https://docs.snowflake.com/en/)
    """)
    processor = gr.State(delete_callback=free_resources)

    with gr.Row():
        chatbot = gr.Chatbot(label="SQL Processor", height=400)
    with gr.Group():
        with gr.Row():
            message = gr.Textbox(
                show_label=False, 
                placeholder="Enter your request. Example: Process SQL file at sqlfiles/wealthmgmt_sql_ddl.txt using nomenclature at bankingnomenclature/naming_conventions.txt"
            )
        with gr.Row():
            success_criteria = gr.Textbox(
                show_label=False, 
                placeholder="What are your success criteria? (Optional - defaults to standard processing)"
            )
    with gr.Row():
        reset_button = gr.Button("Reset", variant="stop")
        go_button = gr.Button("Process SQL", variant="primary")

    ui.load(setup, [], [processor])
    message.submit(
        process_message, [processor, message, success_criteria, chatbot], [chatbot, processor]
    )
    success_criteria.submit(
        process_message, [processor, message, success_criteria, chatbot], [chatbot, processor]
    )
    go_button.click(
        process_message, [processor, message, success_criteria, chatbot], [chatbot, processor]
    )
    reset_button.click(reset, [], [message, success_criteria, chatbot, processor])


ui.launch(inbrowser=True, theme=gr.themes.Default(primary_hue="blue"))

