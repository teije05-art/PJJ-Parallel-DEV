"""
Tool Definitions for Fireworks Function Calling

Defines all tools available to Llama via Fireworks' function calling API.
These tool definitions are passed to Fireworks when making API calls.
"""

# Tool definitions in Fireworks/OpenAI format
LLAMA_PLANNER_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search_memory",
            "description": "Search selected memory entities for relevant information. Always call this FIRST before any online research. Returns memory content, coverage percentage, and identified gaps.",
            "parameters": {
                "type": "object",
                "properties": {
                    "entities": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of memory entity names to search (without .md extension). These are user-selected entities for this goal."
                    },
                    "queries": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Specific queries/topics to search for in the memory entities. Be specific, e.g. 'Current ARR and customer count' not 'information about company'"
                    }
                },
                "required": ["entities", "queries"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "research",
            "description": "Iteratively search online for information to fill gaps identified in memory search. Searches are iterative - each result can inform the next search query. Optimized for finding key data and numbers.",
            "parameters": {
                "type": "object",
                "properties": {
                    "gaps": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Specific gaps/questions that need online research. Be very specific, e.g. 'Q1 2025 SaaS growth trends and PLG methodology' not just 'market information'"
                    },
                    "max_iterations": {
                        "type": "integer",
                        "description": "Maximum number of search iterations (default 3). Each iteration can generate a new search based on findings.",
                        "default": 3,
                        "minimum": 1,
                        "maximum": 5
                    }
                },
                "required": ["gaps"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "call_planner",
            "description": "Call PlannerAgent to create a strategic plan. Provide the goal, gathered context (from memory and research), and your suggested approach/methodology.",
            "parameters": {
                "type": "object",
                "properties": {
                    "goal": {
                        "type": "string",
                        "description": "The user's goal or request"
                    },
                    "context": {
                        "type": "string",
                        "description": "Combined context from memory search and research findings. Can be plain text or formatted summary."
                    },
                    "approach": {
                        "type": "string",
                        "description": "Optional: Your suggested approach or methodology for the plan. E.g. 'Focus on PLG methodology given market trends' or 'Use agile approach considering budget constraints'"
                    }
                },
                "required": ["goal", "context"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "call_verifier",
            "description": "Call VerifierAgent to validate and improve a plan. Only call this if plan quality/feasibility is important.",
            "parameters": {
                "type": "object",
                "properties": {
                    "plan": {
                        "type": "string",
                        "description": "The plan to verify"
                    },
                    "context": {
                        "type": "string",
                        "description": "Context about the goal and constraints (budget, time, resources)"
                    },
                    "criteria": {
                        "type": "string",
                        "description": "Optional: Specific validation criteria. E.g. 'Must be achievable with $50K budget and 2 person team'"
                    }
                },
                "required": ["plan", "context"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "call_executor",
            "description": "Call ExecutorAgent to create implementation details from a plan. Only call this if execution steps matter.",
            "parameters": {
                "type": "object",
                "properties": {
                    "plan": {
                        "type": "string",
                        "description": "The plan to implement"
                    },
                    "context": {
                        "type": "string",
                        "description": "Context about available resources and constraints"
                    },
                    "resources": {
                        "type": "string",
                        "description": "Optional: Description of available resources (budget, team, timeline, tools)"
                    }
                },
                "required": ["plan", "context"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "call_generator",
            "description": "Call GeneratorAgent to synthesize results from multiple sources. Only call this if combining complex data from multiple agents.",
            "parameters": {
                "type": "object",
                "properties": {
                    "data": {
                        "type": "string",
                        "description": "All the data to synthesize (from memory search, research, agent results). Can include JSON or formatted text."
                    },
                    "format": {
                        "type": "string",
                        "description": "Output format desired: 'summary', 'detailed', 'executive_summary', 'action_items', etc.",
                        "default": "summary"
                    }
                },
                "required": ["data"]
            }
        }
    }
]


def get_tool_definitions():
    """
    Return tool definitions for Fireworks API call.

    Usage in simple_chatbox.py:
        tools = get_tool_definitions()
        response = client.chat.completions.create(
            model="accounts/fireworks/models/llama-v3p3-70b-instruct",
            messages=messages,
            tools=tools,
            tool_choice="auto"
        )
    """
    return LLAMA_PLANNER_TOOLS


def get_tool_names():
    """Return list of available tool names."""
    return [tool["function"]["name"] for tool in LLAMA_PLANNER_TOOLS]


def get_tool_by_name(name):
    """Get a specific tool definition by name."""
    for tool in LLAMA_PLANNER_TOOLS:
        if tool["function"]["name"] == name:
            return tool
    return None


if __name__ == "__main__":
    print("Available tools:")
    for tool in LLAMA_PLANNER_TOOLS:
        print(f"  - {tool['function']['name']}: {tool['function']['description'][:60]}...")
