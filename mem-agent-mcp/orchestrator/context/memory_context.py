"""
Memory Context Provider

Handles memory retrieval for patterns, history, and performance metrics.
Single Responsibility: Retrieve learned patterns and execution history from memory.
"""


class MemoryContextProvider:
    """
    Provides context from memory system.

    Retrieves successful patterns, error patterns, execution history,
    and agent performance metrics from the memagent memory system.
    """

    def __init__(self):
        """Initialize memory context provider"""
        pass

    def retrieve_successful_patterns(self, agent) -> str:
        """
        Retrieve successful planning patterns from memory.

        Uses intelligent truncation to keep context focused without extra LLM calls.

        Args:
            agent: The memagent instance for memory retrieval

        Returns:
            Successful patterns as formatted string (intelligently truncated)
        """
        try:
            response = agent.chat("""
                OPERATION: RETRIEVE
                ENTITY: successful_patterns
                CONTEXT: Review successful planning approaches across all agents

                What planning patterns have worked well across all 4 agents?
                What approaches led to successful workflow outcomes?
                What agent coordination strategies proved effective?
            """)

            patterns = response.reply or "No successful patterns yet (first iteration)"

            # Intelligent truncation: keep first 3000 chars (avoids context bloat, no extra LLM call)
            if len(patterns) > 3000:
                # Truncate and add indicator
                patterns = patterns[:3000] + "\n[... patterns truncated for context efficiency ...]"

            return patterns

        except Exception as e:
            print(f"   ⚠️ Pattern retrieval failed: {e}")
            return "Pattern retrieval failed"

    def retrieve_error_patterns(self, agent) -> str:
        """
        Retrieve error patterns from memory.

        Uses intelligent truncation to avoid context bloat without extra LLM calls.

        Args:
            agent: The memagent instance for memory retrieval

        Returns:
            Error patterns to avoid as formatted string (intelligently truncated)
        """
        try:
            response = agent.chat("""
                OPERATION: RETRIEVE
                ENTITY: planning_errors
                CONTEXT: Review planning mistakes across all agents

                What planning approaches have been rejected across all agents?
                What common mistakes should be avoided in agent coordination?
                What workflow patterns led to failures?
            """)

            errors = response.reply or "No errors yet (no failures)"

            # Intelligent truncation: keep first 2000 chars (avoids context bloat, no extra LLM call)
            if len(errors) > 2000:
                # Truncate and add indicator
                errors = errors[:2000] + "\n[... errors truncated for context efficiency ...]"

            return errors

        except Exception as e:
            print(f"   ⚠️ Error pattern retrieval failed: {e}")
            return "Error pattern retrieval failed"

    def retrieve_execution_history(self, agent) -> str:
        """
        Retrieve execution history from memory.

        Uses intelligent truncation to keep context focused without extra LLM calls.

        Args:
            agent: The memagent instance for memory retrieval

        Returns:
            Execution history as formatted string (intelligently truncated)
        """
        try:
            response = agent.chat("""
                OPERATION: RETRIEVE
                ENTITY: execution_log
                CONTEXT: Review past enhanced iterations and workflows

                What enhanced workflows have been successfully executed?
                How many iterations have completed with agent coordination?
                What were the outcomes of previous agentic workflows?
            """)

            history = response.reply or "No history yet (first iteration)"

            # Intelligent truncation: keep first 2500 chars (avoids context bloat, no extra LLM call)
            if len(history) > 2500:
                # Truncate and add indicator
                history = history[:2500] + "\n[... history truncated for context efficiency ...]"

            return history

        except Exception as e:
            print(f"   ⚠️ History retrieval failed: {e}")
            return "Execution history retrieval failed"

    def retrieve_agent_performance(self, agent) -> str:
        """
        Retrieve agent performance metrics from memory.

        Args:
            agent: The memagent instance for memory retrieval

        Returns:
            Agent performance metrics as formatted string
        """
        try:
            response = agent.chat("""
                OPERATION: RETRIEVE
                ENTITY: agent_performance
                CONTEXT: Review agent performance and learning progress

                What are the current performance metrics for each agent?
                How has Flow-GRPO training improved planning over time?
                What agent-specific improvements have been observed?
            """)
            return response.reply or "No performance data yet (first iteration)"
        except:
            return "Performance data retrieval failed"
