from typing import Annotated
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from dotenv import load_dotenv
from langgraph.prebuilt import ToolNode
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from typing import List, Any, Optional, Dict
from pydantic import BaseModel, Field
from sql_processor_tools import sql_processor_tools
import uuid
import asyncio
from datetime import datetime

load_dotenv(override=True)


class State(TypedDict):
    """
    State dictionary for the LangGraph workflow.
    
    This TypedDict defines the structure of state that flows through the graph nodes.
    It maintains conversation history, success criteria, feedback, and workflow control flags.
    
    Attributes:
        messages: List of conversation messages (annotated with add_messages for LangGraph)
        success_criteria: String describing what constitutes successful completion
        feedback_on_work: Optional feedback from evaluator on previous attempts
        success_criteria_met: Boolean flag indicating if success criteria has been achieved
        user_input_needed: Boolean flag indicating if user clarification is required
    """
    messages: Annotated[List[Any], add_messages]
    success_criteria: str
    feedback_on_work: Optional[str]
    success_criteria_met: bool
    user_input_needed: bool


class EvaluatorOutput(BaseModel):
    """
    Structured output model for the evaluator LLM.
    
    The evaluator uses this model to provide structured feedback on whether
    the worker's response meets the success criteria and if user input is needed.
    
    Attributes:
        feedback: Detailed feedback on the assistant's response
        success_criteria_met: Whether the success criteria have been met
        user_input_needed: True if more input is needed from the user, clarifications, or if assistant is stuck
    """
    feedback: str = Field(description="Feedback on the assistant's response")
    success_criteria_met: bool = Field(description="Whether the success criteria have been met")
    user_input_needed: bool = Field(
        description="True if more input is needed from the user, or clarifications, or the assistant is stuck"
    )


class SQLProcessor:
    """
    Main SQL Processor class implementing LangGraph workflow for processing SQL files.
    
    This class orchestrates the processing of SQL files for banking data warehouses using
    a worker-evaluator pattern. It reads SQL files, applies banking nomenclature, validates
    Snowflake compliance, and generates separate DDL and DML files with comprehensive
    banking controls and audit comments.
    
    The workflow follows this pattern:
    1. Worker node processes the request using LLM with tools
    2. Tools execute (read files, parse SQL, generate output files)
    3. Evaluator node checks if success criteria is met
    4. Loop continues until criteria met or user input needed
    
    Attributes:
        worker_llm_with_tools: LLM instance bound with SQL processing tools
        evaluator_llm_with_output: LLM instance with structured output for evaluation
        tools: List of available tools for SQL processing
        graph: Compiled LangGraph workflow
        processor_id: Unique identifier for this processor instance
        memory: MemorySaver for checkpointing conversation state
    """
    def __init__(self):
        """
        Initialize SQLProcessor instance.
        
        Creates a new processor with unique ID and memory checkpointing.
        Call setup() after initialization to configure LLMs and build the graph.
        """
        self.worker_llm_with_tools = None
        self.evaluator_llm_with_output = None
        self.tools = None
        self.llm_with_tools = None
        self.graph = None
        self.processor_id = str(uuid.uuid4())
        self.memory = MemorySaver()

    async def setup(self):
        """
        Initialize and configure the SQL processor.
        
        Sets up LLM instances, loads tools, and builds the LangGraph workflow.
        Must be called before using the processor.
        
        Raises:
            Exception: If tool loading or graph building fails
        """
        self.tools = await sql_processor_tools()
        worker_llm = ChatOpenAI(model="gpt-4o-mini")
        self.worker_llm_with_tools = worker_llm.bind_tools(self.tools)
        evaluator_llm = ChatOpenAI(model="gpt-4o-mini")
        self.evaluator_llm_with_output = evaluator_llm.with_structured_output(EvaluatorOutput)
        await self.build_graph()

    def worker(self, state: State) -> Dict[str, Any]:
        """
        Worker node that processes user requests using LLM and tools.
        
        This is the main processing node that:
        - Constructs system prompts with task instructions and success criteria
        - Invokes the LLM with access to SQL processing tools
        - Handles feedback from previous evaluation attempts
        - Returns LLM response for routing to tools or evaluator
        
        The worker is instructed to:
        - Read SQL and nomenclature files
        - Parse SQL into DDL/DML
        - Apply banking nomenclature
        - Ensure Snowflake compliance
        - Generate separate DDL/DML files with banking controls
        
        Args:
            state: Current workflow state containing messages and success criteria
            
        Returns:
            Dictionary with updated messages containing LLM response
        """
        system_message = f"""You are a specialized SQL processor assistant that processes SQL files for banking data warehouses.
    Your primary tasks are:
    1. Read SQL files from relative or absolute paths
    2. Read banking nomenclature files from relative or absolute paths
    3. Parse SQL statements into DDL (Data Definition Language) and DML (Data Manipulation Language)
    4. Apply banking nomenclature conventions to SQL statements
    5. Generate separate DDL and DML files with comprehensive comments and banking controls
    6. Ensure all generated files are ready for execution and audit compliance
    7. CRITICAL: Ensure ALL SQL statements are compliant with Snowflake documentation at https://docs.snowflake.com/en/
    
    You have access to tools that can:
    - Read SQL files from relative or absolute paths
    - Read banking nomenclature files from relative or absolute paths
    - Process SQL files and generate separate DDL/DML files with banking controls
    - Get file contents for detailed analysis
    - Validate Snowflake SQL syntax compliance
    
    When processing SQL files:
    - Always read both the SQL file and nomenclature file first
    - Parse SQL statements correctly into DDL and DML
    - Apply banking nomenclature rules consistently
    - CRITICAL: Ensure all SQL syntax follows Snowflake documentation standards:
      * Use Snowflake-specific data types (VARCHAR, NUMBER, TIMESTAMP_NTZ, etc.)
      * Use Snowflake-specific functions and syntax
      * Follow Snowflake naming conventions (case-sensitive identifiers when quoted)
      * Use Snowflake-specific DDL syntax (CREATE OR REPLACE, IF NOT EXISTS, etc.)
      * Use Snowflake-specific DML syntax (MERGE, COPY INTO, etc.)
      * Avoid unsupported features (CHECK constraints in some contexts, certain indexes, etc.)
      * Use proper Snowflake schema and database references
    - Add comprehensive comments including:
      * Banking control notes
      * Audit trail information
      * Execution instructions
      * Compliance notes
      * Snowflake-specific implementation notes
    - Generate separate files for DDL and DML
    - Ensure files are ready for execution and auditing in Snowflake
    
    The current date and time is {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

    This is the success criteria:
    {state["success_criteria"]}
    
    You should reply either with a question for the user about this assignment, or with your final response.
    If you have a question for the user, you need to reply by clearly stating your question. An example might be:

    Question: please provide the paths (relative or absolute) to the SQL file and banking nomenclature file

    If you've finished, reply with the final answer, and don't ask a question; simply reply with the answer.
    """

        if state.get("feedback_on_work"):
            system_message += f"""
    Previously you thought you completed the assignment, but your reply was rejected because the success criteria was not met.
    Here is the feedback on why this was rejected:
    {state["feedback_on_work"]}
    With this feedback, please continue the assignment, ensuring that you meet the success criteria or have a question for the user."""

        # Add in the system message
        found_system_message = False
        messages = state["messages"]
        for message in messages:
            if isinstance(message, SystemMessage):
                message.content = system_message
                found_system_message = True

        if not found_system_message:
            messages = [SystemMessage(content=system_message)] + messages

        # Invoke the LLM with tools
        response = self.worker_llm_with_tools.invoke(messages)

        # Return updated state
        return {
            "messages": [response],
        }

    def worker_router(self, state: State) -> str:
        """
        Route worker output to either tools or evaluator.
        
        Checks if the last message from worker contains tool calls.
        If tools are needed, routes to "tools" node; otherwise to "evaluator".
        
        Args:
            state: Current workflow state
            
        Returns:
            "tools" if tool calls are present, "evaluator" otherwise
        """
        last_message = state["messages"][-1]

        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            return "tools"
        else:
            return "evaluator"

    def format_conversation(self, messages: List[Any]) -> str:
        """
        Format conversation messages into readable text string.
        
        Converts list of message objects into a formatted string showing
        the conversation history between user and assistant.
        
        Args:
            messages: List of message objects (HumanMessage, AIMessage, etc.)
            
        Returns:
            Formatted string representation of the conversation
        """
        conversation = "Conversation history:\n\n"
        for message in messages:
            if isinstance(message, HumanMessage):
                conversation += f"User: {message.content}\n"
            elif isinstance(message, AIMessage):
                text = message.content or "[Tools use]"
                conversation += f"Assistant: {text}\n"
        return conversation

    def evaluator(self, state: State) -> State:
        """
        Evaluator node that checks if success criteria has been met.
        
        This node:
        - Reviews the worker's response against success criteria
        - Verifies Snowflake compliance of generated SQL
        - Checks if banking nomenclature was applied
        - Determines if user input is needed
        - Provides structured feedback
        
        CRITICAL: The evaluator must verify that all SQL statements comply with
        Snowflake documentation at https://docs.snowflake.com/en/
        
        Args:
            state: Current workflow state with worker's response
            
        Returns:
            Updated state with evaluator feedback and flags for success/user_input_needed
        """
        last_response = state["messages"][-1].content

        system_message = """You are an evaluator that determines if a task has been completed successfully by an Assistant.
    Assess the Assistant's last response based on the given criteria. Respond with your feedback, and with your decision on whether the success criteria has been met,
    and whether more input is needed from the user.
    
    CRITICAL: You must verify that all generated SQL DDL and DML statements are compliant with Snowflake documentation at https://docs.snowflake.com/en/.
    Reject any work that does not follow Snowflake syntax, data types, and best practices."""

        user_message = f"""You are evaluating a conversation between the User and Assistant. You decide what action to take based on the last response from the Assistant.

    The entire conversation with the assistant, with the user's original request and all replies, is:
    {self.format_conversation(state["messages"])}

    The success criteria for this assignment is:
    {state["success_criteria"]}

    And the final response from the Assistant that you are evaluating is:
    {last_response}

    Respond with your feedback, and decide if the success criteria is met by this response.
    Also, decide if more user input is required, either because the assistant has a question, needs clarification, or seems to be stuck and unable to answer without help.

    CRITICAL EVALUATION REQUIREMENT: You MUST verify that all generated SQL DDL and DML statements are compliant with Snowflake documentation at https://docs.snowflake.com/en/
    
    The Assistant has access to tools to read files, process SQL files, and generate DDL/DML files. If the Assistant says they have processed files and generated DDL/DML files with banking controls, then you can assume they have done so. 
    However, you MUST verify Snowflake compliance. Reject the work if:
    - The SQL files were not properly separated into DDL and DML
    - Banking nomenclature was not applied
    - Comments and banking controls were not added
    - Files are not ready for execution and audit
    - CRITICAL: SQL syntax is not compliant with Snowflake documentation (https://docs.snowflake.com/en/)
      * Uses non-Snowflake data types or syntax
      * Uses unsupported features (like certain CHECK constraints, traditional indexes, etc.)
      * Does not follow Snowflake-specific DDL/DML patterns
      * Uses database-specific features not available in Snowflake
      * Missing Snowflake-specific syntax (CREATE OR REPLACE, IF NOT EXISTS, etc.)
      * Improper use of Snowflake identifiers (case sensitivity, quoting)
      * Uses unsupported SQL functions or operations
    
    Reference Snowflake documentation at https://docs.snowflake.com/en/ to verify compliance.
    """

        if state["feedback_on_work"]:
            user_message += f"Also, note that in a prior attempt from the Assistant, you provided this feedback: {state['feedback_on_work']}\n"
            user_message += "If you're seeing the Assistant repeating the same mistakes, then consider responding that user input is required."

        evaluator_messages = [
            SystemMessage(content=system_message),
            HumanMessage(content=user_message),
        ]

        eval_result = self.evaluator_llm_with_output.invoke(evaluator_messages)
        new_state = {
            "messages": [
                {
                    "role": "assistant",
                    "content": f"Evaluator Feedback on this answer: {eval_result.feedback}",
                }
            ],
            "feedback_on_work": eval_result.feedback,
            "success_criteria_met": eval_result.success_criteria_met,
            "user_input_needed": eval_result.user_input_needed,
        }
        return new_state

    def route_based_on_evaluation(self, state: State) -> str:
        """
        Route based on evaluation results.
        
        Determines next step in workflow:
        - If success criteria met OR user input needed -> END
        - Otherwise -> Continue to worker for another attempt
        
        Args:
            state: Current workflow state with evaluation results
            
        Returns:
            "END" if complete or needs user input, "worker" to continue processing
        """
        if state["success_criteria_met"] or state["user_input_needed"]:
            return "END"
        else:
            return "worker"

    async def build_graph(self):
        """
        Build and compile the LangGraph workflow.
        
        Constructs the graph with three nodes:
        - worker: Processes requests with LLM and tools
        - tools: Executes tool calls from worker
        - evaluator: Evaluates if success criteria is met
        
        Graph flow:
        START -> worker -> (tools or evaluator)
        tools -> worker (loop back)
        evaluator -> (worker or END)
        
        The graph uses memory checkpointing to maintain conversation state.
        """
        # Set up Graph Builder with State
        graph_builder = StateGraph(State)

        # Add nodes
        graph_builder.add_node("worker", self.worker)
        graph_builder.add_node("tools", ToolNode(tools=self.tools))
        graph_builder.add_node("evaluator", self.evaluator)

        # Add edges
        graph_builder.add_conditional_edges(
            "worker", self.worker_router, {"tools": "tools", "evaluator": "evaluator"}
        )
        graph_builder.add_edge("tools", "worker")
        graph_builder.add_conditional_edges(
            "evaluator", self.route_based_on_evaluation, {"worker": "worker", "END": END}
        )
        graph_builder.add_edge(START, "worker")

        # Compile the graph
        self.graph = graph_builder.compile(checkpointer=self.memory)

    async def run_superstep(self, message, success_criteria, history):
        """
        Execute one processing step through the LangGraph workflow.
        
        Invokes the graph with user message and success criteria, then formats
        the results into conversation history format for the UI.
        
        Args:
            message: User's input message/request
            success_criteria: Optional success criteria (uses default if None)
            history: Previous conversation history
            
        Returns:
            Updated conversation history with user message, assistant reply, and evaluator feedback
        """
        config = {"configurable": {"thread_id": self.processor_id}}

        state = {
            "messages": message,
            "success_criteria": success_criteria or "Process SQL file, apply banking nomenclature, and generate separate DDL and DML files with banking controls and comments. CRITICAL: All SQL statements must be compliant with Snowflake documentation at https://docs.snowflake.com/en/. Files must be ready for execution in Snowflake and audit.",
            "feedback_on_work": None,
            "success_criteria_met": False,
            "user_input_needed": False,
        }
        result = await self.graph.ainvoke(state, config=config)
        user = {"role": "user", "content": message}
        reply = {"role": "assistant", "content": result["messages"][-2].content}
        feedback = {"role": "assistant", "content": result["messages"][-1].content}
        return history + [user, reply, feedback]

    def cleanup(self):
        """
        Cleanup resources when processor is no longer needed.
        
        Currently a placeholder for future resource cleanup if needed.
        Called automatically when processor state is deleted in Gradio.
        """
        pass

