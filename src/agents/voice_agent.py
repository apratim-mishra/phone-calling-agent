from typing import TypedDict, Annotated, Sequence, Literal
import operator

from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, SystemMessage
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode

from src.agents.prompts import SYSTEM_PROMPT, GREETING_PROMPT
from src.agents.tools import AVAILABLE_TOOLS
from src.models.provider import get_llm
from src.utils.logging import get_logger

logger = get_logger(__name__)


class AgentState(TypedDict):
    """State for the voice agent conversation."""

    messages: Annotated[Sequence[BaseMessage], operator.add]
    call_sid: str
    caller_number: str
    current_action: Literal["continue", "transfer", "end"]


class VoiceAgent:
    """LangGraph-based voice agent for phone conversations."""

    def __init__(self):
        self.llm_provider = get_llm()
        self.tools = AVAILABLE_TOOLS
        self._graph = None

    def _build_graph(self) -> StateGraph:
        """Build the LangGraph state machine."""
        model = self.llm_provider.get_model()
        model_with_tools = model.bind_tools(self.tools)

        async def agent_node(state: AgentState) -> dict:
            """Process user input and generate response."""
            messages = list(state["messages"])

            if not any(isinstance(m, SystemMessage) for m in messages):
                messages.insert(0, SystemMessage(content=SYSTEM_PROMPT))

            response = await model_with_tools.ainvoke(messages)

            action = "continue"
            if response.content:
                content_lower = response.content.lower()
                if "TRANSFER_REQUESTED" in str(response.content):
                    action = "transfer"
                elif "CALL_ENDED" in str(response.content):
                    action = "end"

            return {
                "messages": [response],
                "current_action": action,
            }

        def should_continue(state: AgentState) -> Literal["tools", "end"]:
            """Determine if we should continue to tools or end."""
            last_message = state["messages"][-1]

            if hasattr(last_message, "tool_calls") and last_message.tool_calls:
                return "tools"

            return "end"

        tool_node = ToolNode(self.tools)

        graph = StateGraph(AgentState)
        graph.add_node("agent", agent_node)
        graph.add_node("tools", tool_node)

        graph.set_entry_point("agent")
        graph.add_conditional_edges(
            "agent",
            should_continue,
            {
                "tools": "tools",
                "end": END,
            },
        )
        graph.add_edge("tools", "agent")

        return graph.compile()

    @property
    def graph(self):
        """Get or create the compiled graph."""
        if self._graph is None:
            self._graph = self._build_graph()
        return self._graph

    async def process_message(
        self,
        user_input: str,
        call_sid: str,
        caller_number: str,
        history: list[BaseMessage] | None = None,
    ) -> tuple[str, list[BaseMessage], str]:
        """Process a user message and return the response.

        Args:
            user_input: Transcribed user speech
            call_sid: Twilio call SID
            caller_number: Caller's phone number
            history: Previous conversation messages

        Returns:
            Tuple of (response_text, updated_history, action)
        """
        messages = history or []
        messages.append(HumanMessage(content=user_input))

        state: AgentState = {
            "messages": messages,
            "call_sid": call_sid,
            "caller_number": caller_number,
            "current_action": "continue",
        }

        result = await self.graph.ainvoke(state)

        response_messages = result["messages"]
        last_ai_message = None
        for msg in reversed(response_messages):
            if isinstance(msg, AIMessage) and msg.content:
                last_ai_message = msg
                break

        response_text = last_ai_message.content if last_ai_message else ""
        action = result.get("current_action", "continue")

        if "TRANSFER_REQUESTED" in response_text:
            response_text = (
                "I understand. Let me transfer you to one of our human agents. "
                "Please hold for just a moment."
            )
            action = "transfer"
        elif "CALL_ENDED" in response_text:
            response_text = (
                "Thank you for calling Premier Properties! "
                "Feel free to call back anytime. Have a wonderful day!"
            )
            action = "end"

        logger.debug(f"Agent response: {response_text[:100]}... (action: {action})")

        return response_text, list(response_messages), action

    async def get_greeting(self) -> str:
        """Get the initial greeting message."""
        return GREETING_PROMPT

    def reset(self) -> None:
        """Reset the agent state."""
        self._graph = None

