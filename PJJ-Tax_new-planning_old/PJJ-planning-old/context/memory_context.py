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

    def retrieve_successful_patterns(self, agent, selected_plans=None) -> str:
        """
        Retrieve successful planning patterns from memory.

        CONSTRAINT: If selected_plans provided, reads content from ONLY those plan files.
        Uses direct file reads instead of agent queries to avoid full-system searches.

        Args:
            agent: The memagent instance for memory retrieval
            selected_plans: Optional list of plan names - if provided, reads ONLY these files

        Returns:
            Successful patterns as formatted string from selected plans
        """
        from pathlib import Path

        # USER-DEFINED CONSTRAINT BOUNDARIES:
        # If user selected specific plans, read ONLY those plan files
        # If no plans selected, return empty (don't search broadly)
        if selected_plans is not None and not selected_plans:
            return ""

        try:
            if selected_plans:
                # DIRECT FILE READ: Read selected plan files from disk (not agent query)
                plans_content = []
                plans_path = Path(agent.memory_path).parent / "plans"

                for plan_name in selected_plans:
                    plan_file = plans_path / plan_name
                    if plan_file.exists():
                        try:
                            content = plan_file.read_text(encoding='utf-8')
                            # Extract key insights from plan (first 500 chars)
                            summary = content[:500].replace('\n', ' ')
                            plans_content.append(f"• {plan_name}: {summary}...")
                        except Exception as e:
                            plans_content.append(f"• {plan_name}: [Error reading file: {e}]")
                    else:
                        plans_content.append(f"• {plan_name}: [File not found]")

                patterns = f"Patterns from {len(selected_plans)} selected plans:\n" + "\n".join(plans_content)
            else:
                # No specific plans - return empty to avoid full system search
                patterns = "No patterns (no plans selected for learning)"

            # Intelligent truncation: keep first 3000 chars
            if len(patterns) > 3000:
                patterns = patterns[:3000] + "\n[... patterns truncated for context efficiency ...]"

            return patterns

        except Exception as e:
            print(f"   ⚠️ Pattern retrieval failed: {e}")
            return f"Pattern retrieval failed: {e}"

    def retrieve_error_patterns(self, agent, selected_plans=None) -> str:
        """
        Retrieve error patterns from memory.

        CONSTRAINT: If selected_plans provided, ONLY analyzes those plans.
        Uses intelligent truncation to avoid context bloat without extra LLM calls.

        Args:
            agent: The memagent instance for memory retrieval
            selected_plans: Optional list of plan names - if provided, ONLY searches these plans

        Returns:
            Error patterns to avoid as formatted string (intelligently truncated)
        """
        from pathlib import Path

        # USER-DEFINED CONSTRAINT BOUNDARIES:
        # If user selected specific plans, search ONLY within those plans
        # If no plans selected, return empty (don't search broadly)
        if selected_plans is not None and not selected_plans:
            return ""

        try:
            if selected_plans:
                # DIRECT FILE READ: Read selected plan files from disk (not agent query)
                plans_content = []
                plans_path = Path(agent.memory_path).parent / "plans"

                for plan_name in selected_plans:
                    plan_file = plans_path / plan_name
                    if plan_file.exists():
                        try:
                            content = plan_file.read_text(encoding='utf-8')
                            # Extract error patterns from plan (first 800 chars to get errors/mistakes section)
                            summary = content[:800].replace('\n', ' ')
                            plans_content.append(f"• {plan_name}: {summary}...")
                        except Exception as e:
                            plans_content.append(f"• {plan_name}: [Error reading file: {e}]")
                    else:
                        plans_content.append(f"• {plan_name}: [File not found]")

                errors = f"Error patterns from {len(selected_plans)} selected plans:\n" + "\n".join(plans_content)
            else:
                # No specific plans - return empty to avoid full system search
                errors = "No error patterns (no plans selected for learning)"

            # Intelligent truncation: keep first 2000 chars (avoids context bloat, no extra LLM call)
            if len(errors) > 2000:
                errors = errors[:2000] + "\n[... errors truncated for context efficiency ...]"

            return errors

        except Exception as e:
            print(f"   ⚠️ Error pattern retrieval failed: {e}")
            return "Error pattern retrieval failed"

    def retrieve_execution_history(self, agent, selected_plans=None) -> str:
        """
        Retrieve execution history from memory.

        CONSTRAINT: If selected_plans provided, ONLY analyzes those plans.
        Uses intelligent truncation to keep context focused without extra LLM calls.

        Args:
            agent: The memagent instance for memory retrieval
            selected_plans: Optional list of plan names - if provided, ONLY searches these plans

        Returns:
            Execution history as formatted string (intelligently truncated)
        """
        from pathlib import Path

        # USER-DEFINED CONSTRAINT BOUNDARIES:
        # If user selected specific plans, search ONLY within those plans
        # If no plans selected, return empty (don't search broadly)
        if selected_plans is not None and not selected_plans:
            return ""

        try:
            if selected_plans:
                # DIRECT FILE READ: Read selected plan files from disk (not agent query)
                plans_content = []
                plans_path = Path(agent.memory_path).parent / "plans"

                for plan_name in selected_plans:
                    plan_file = plans_path / plan_name
                    if plan_file.exists():
                        try:
                            content = plan_file.read_text(encoding='utf-8')
                            # Extract execution history from plan (first 1000 chars for outcomes)
                            summary = content[:1000].replace('\n', ' ')
                            plans_content.append(f"• {plan_name}: {summary}...")
                        except Exception as e:
                            plans_content.append(f"• {plan_name}: [Error reading file: {e}]")
                    else:
                        plans_content.append(f"• {plan_name}: [File not found]")

                history = f"Execution history from {len(selected_plans)} selected plans:\n" + "\n".join(plans_content)
            else:
                # No specific plans - return empty to avoid full system search
                history = "No execution history (no plans selected for learning)"

            # Intelligent truncation: keep first 2500 chars (avoids context bloat, no extra LLM call)
            if len(history) > 2500:
                history = history[:2500] + "\n[... history truncated for context efficiency ...]"

            return history

        except Exception as e:
            print(f"   ⚠️ History retrieval failed: {e}")
            return "Execution history retrieval failed"

    def retrieve_agent_performance(self, agent, selected_plans=None) -> str:
        """
        Retrieve agent performance metrics from memory.

        CONSTRAINT: If selected_plans provided, ONLY analyzes those plans.

        Args:
            agent: The memagent instance for memory retrieval
            selected_plans: Optional list of plan names - if provided, ONLY searches these plans

        Returns:
            Agent performance metrics as formatted string
        """
        from pathlib import Path

        # USER-DEFINED CONSTRAINT BOUNDARIES:
        # If user selected specific plans, search ONLY within those plans
        # If no plans selected, return empty (don't search broadly)
        if selected_plans is not None and not selected_plans:
            return ""

        try:
            if selected_plans:
                # DIRECT FILE READ: Read selected plan files from disk (not agent query)
                plans_content = []
                plans_path = Path(agent.memory_path).parent / "plans"

                for plan_name in selected_plans:
                    plan_file = plans_path / plan_name
                    if plan_file.exists():
                        try:
                            content = plan_file.read_text(encoding='utf-8')
                            # Extract performance metrics from plan (first 600 chars)
                            summary = content[:600].replace('\n', ' ')
                            plans_content.append(f"• {plan_name}: {summary}...")
                        except Exception as e:
                            plans_content.append(f"• {plan_name}: [Error reading file: {e}]")
                    else:
                        plans_content.append(f"• {plan_name}: [File not found]")

                performance = f"Agent performance from {len(selected_plans)} selected plans:\n" + "\n".join(plans_content)
            else:
                # No specific plans - return empty to avoid full system search
                performance = "No performance data (no plans selected for learning)"

            # Intelligent truncation: keep first 2000 chars
            if len(performance) > 2000:
                performance = performance[:2000] + "\n[... performance data truncated for context efficiency ...]"

            return performance
        except Exception as e:
            return f"Performance data retrieval failed: {e}"
