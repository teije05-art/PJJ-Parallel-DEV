#!/usr/bin/env python3
"""
Diagnostic script to identify import failures in the system.
Run: python diagnose_imports.py
"""

import sys
import os
from pathlib import Path

# Add repo to path
REPO_ROOT = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, REPO_ROOT)

print("=" * 80)
print("IMPORT DIAGNOSTIC TOOL")
print("=" * 80)
print()

# Test 1: Agent import
print("TEST 1: Agent import")
try:
    from agent.agent import Agent
    print("✅ agent.agent.Agent imported successfully")
except Exception as e:
    print(f"❌ agent.agent.Agent failed: {e}")
    import traceback
    traceback.print_exc()

print()

# Test 2: Research Agent
print("TEST 2: ResearchAgent import")
try:
    from research_agent import ResearchAgent, ResearchResult
    print("✅ research_agent imported successfully")
except Exception as e:
    print(f"❌ research_agent failed: {e}")
    import traceback
    traceback.print_exc()

print()

# Test 3: Orchestrator.agents
print("TEST 3: orchestrator.agents import")
try:
    from orchestrator.agents import (
        PlannerAgent,
        VerifierAgent,
        ExecutorAgent,
        GeneratorAgent,
        BaseAgent,
        AgentResult
    )
    print("✅ orchestrator.agents imported successfully")
except Exception as e:
    print(f"❌ orchestrator.agents failed: {e}")
    import traceback
    traceback.print_exc()

print()

# Test 4: LlamaPlanner
print("TEST 4: LlamaPlanner import (the main issue)")
try:
    from llama_planner import LlamaPlanner, PlanningApproach, PlanningOutcome
    print("✅ llama_planner imported successfully")
except Exception as e:
    print(f"❌ llama_planner failed: {e}")
    import traceback
    traceback.print_exc()

print()

# Test 5: SimpleOrchestrator
print("TEST 5: SimpleOrchestrator import")
try:
    from orchestrator.simple_orchestrator import SimpleOrchestrator
    print("✅ orchestrator.simple_orchestrator imported successfully")
except Exception as e:
    print(f"❌ orchestrator.simple_orchestrator failed: {e}")
    import traceback
    traceback.print_exc()

print()
print("=" * 80)
print("DIAGNOSTIC COMPLETE")
print("=" * 80)
