# emiel&treloar_project
## Project Overview
- Current Setup: MCP server with memagent (memory agent for efficient infinite information storage) + planning orchestrator script
- Goal: Transform into groundbreaking autonomous planner AI that could benefit all of KPMG
- Architecture: Claude frontend → MCP server (running on rented 1x H100 for POC or Apple laptop for testing) → memagent → powered by Llama 3.3 70B (local or via Fireworks API)
- Current Status: Orchestrator implemented but encountering multiple issues, system not strong enough yet
- Key Problem Identified: Plans lack actual detail and produce "AI slop" - need anti-AIslop tool to add substance and differentiation
- Boss's Input: Agreed that additional anti-AIslop tool needed for orchestrator to generate detailed, meaningful plans that set system apart from regular AI
- Context: Working at KPMG as intern, aiming for enterprise-level impact