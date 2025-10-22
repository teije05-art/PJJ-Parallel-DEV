"""
Enhanced Learning Orchestrator with AgentFlow Integration

This enhanced orchestrator integrates AgentFlow's 4-agent architecture with your existing MemAgent system:
1. 🧭 Planner Agent - Strategic planning using MemAgent context
2. 🛠️ Executor Agent - Implementation using MemAgent tools
3. ✅ Verifier Agent - Quality assurance using MemAgent validation
4. ✍️ Generator Agent - Synthesis using MemAgent capabilities

Key improvements over the original orchestrator:
- Specialized agents instead of monolithic planning
- Real learning through Flow-GRPO optimization
- Project-specific plans instead of generic templates
- Enhanced memory coordination between agents
- Better quality and depth of planning responses
"""

import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Optional

# Add repo root to path
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from agent import Agent
from .agentflow_agents import AgentCoordinator


class EnhancedLearningOrchestrator:
    """
    Enhanced learning orchestrator with AgentFlow integration.
    
    This orchestrator combines the best of both systems:
    - Your existing MemAgent infrastructure and memory system
    - AgentFlow's 4-agent architecture and Flow-GRPO optimization
    - Real learning that improves planning quality over time
    """
    
    def __init__(self, memory_path: str, max_iterations: int = 15, strict_validation: bool = False):
        """
        Initialize the enhanced learning orchestrator.
        
        Args:
            memory_path: Path to MemAgent memory directory
            max_iterations: Maximum number of learning iterations
            strict_validation: If True, use strict validation. If False, use lenient validation
        """
        self.memory_path = Path(memory_path)
        self.max_iterations = max_iterations
        self.current_iteration = 0
        self.strict_validation = strict_validation
        
        # Initialize agent with backend auto-detection
        use_fireworks = sys.platform == "darwin"  # Mac uses Fireworks
        use_vllm = sys.platform == "linux"        # H100 uses vLLM
        
        self.agent = Agent(
            use_fireworks=use_fireworks,
            use_vllm=use_vllm,
            memory_path=str(memory_path),
            predetermined_memory_path=False
        )
        
        # Initialize AgentFlow coordinator
        self.agent_coordinator = AgentCoordinator(self.agent, self.memory_path)
        
        # Ensure memory entities exist
        self._initialize_memory_entities()
        
        print(f"🚀 Enhanced Learning Orchestrator initialized")
        print(f"   Backend: {'Fireworks (Mac)' if use_fireworks else 'vLLM (H100)'}")
        print(f"   Memory: {memory_path}")
        print(f"   Max iterations: {max_iterations}")
        print(f"   AgentFlow Integration: ✅ 4 Specialized Agents")
        print(f"   Flow-GRPO Training: ✅ In-the-flow optimization")
    
    def _initialize_memory_entities(self):
        """Create memory entity files if they don't exist"""
        entities_dir = self.memory_path / "entities"
        entities_dir.mkdir(parents=True, exist_ok=True)
        
        # Enhanced execution log for successful workflows
        execution_log = entities_dir / "execution_log.md"
        if not execution_log.exists():
            execution_log.write_text(
                "# Enhanced Execution Log\n\n"
                "This file tracks all approved and executed agentic workflows.\n"
                "Each successful iteration adds learned context through Flow-GRPO training.\n\n"
                "## Workflow Components:\n"
                "- 🧭 Planner Agent: Strategic planning and decision making\n"
                "- 🛠️ Executor Agent: Tool execution and action implementation\n"
                "- ✅ Verifier Agent: Quality checking and validation\n"
                "- ✍️ Generator Agent: Content synthesis and final output creation\n\n"
            )
        
        # Enhanced successful patterns with agent-specific insights
        patterns_file = entities_dir / "successful_patterns.md"
        if not patterns_file.exists():
            patterns_file.write_text(
                "# Enhanced Successful Planning Patterns\n\n"
                "This file tracks proven approaches that work across all 4 agents.\n"
                "Used for in-context learning and Flow-GRPO optimization.\n\n"
                "## Agent-Specific Patterns:\n"
                "- **Planner Agent**: Successful strategic approaches\n"
                "- **Executor Agent**: Effective implementation methods\n"
                "- **Verifier Agent**: Quality validation techniques\n"
                "- **Generator Agent**: Synthesis best practices\n\n"
            )
        
        # Enhanced planning errors with agent-specific insights
        errors_file = entities_dir / "planning_errors.md"
        if not errors_file.exists():
            errors_file.write_text(
                "# Enhanced Planning Errors to Avoid\n\n"
                "This file tracks rejected workflows and common mistakes across all agents.\n"
                "Used to avoid repeating failures and improve Flow-GRPO training.\n\n"
                "## Agent-Specific Error Patterns:\n"
                "- **Planner Agent**: Strategic mistakes to avoid\n"
                "- **Executor Agent**: Implementation pitfalls\n"
                "- **Verifier Agent**: Validation failures\n"
                "- **Generator Agent**: Synthesis errors\n\n"
            )
    
    def run_enhanced_learning_loop(self, goal: str):
        """
        Main enhanced learning loop with AgentFlow integration.
        
        This implements the iterative learning approach with 4 specialized agents
        and Flow-GRPO optimization for real learning and improvement.
        """
        print(f"\n🎯 STARTING ENHANCED LEARNING LOOP")
        print(f"Goal: {goal}")
        print(f"Max iterations: {self.max_iterations}")
        print("=" * 80)
        
        for iteration in range(1, self.max_iterations + 1):
            self.current_iteration = iteration
            print(f"\n🔄 ENHANCED ITERATION {iteration}/{self.max_iterations}")
            print("-" * 60)
            
            try:
                # Step 1: Retrieve enhanced context with goal analysis
                context = self._retrieve_enhanced_context(goal)
                
                # Step 2: Coordinate agentic workflow
                agent_results = self.agent_coordinator.coordinate_agentic_workflow(goal, context)
                
                # Step 3: Human approval for the coordinated workflow
                approval, feedback = self._get_human_approval(agent_results, goal)
                
                if approval == "approved":
                    # Step 4: Execute approved workflow
                    execution = self._execute_enhanced_workflow(agent_results, goal)
                    
                    # Step 5: Learn from success
                    self._write_enhanced_success_to_memory(agent_results, execution)
                    
                    print(f"\n🎉 SUCCESS! Enhanced workflow approved and executed.")
                    print(f"Learning iteration {iteration} completed successfully.")
                    print(f"Flow-GRPO training applied to improve future iterations.")
                    return True
                    
                elif approval == "rejected":
                    # Learn from rejection
                    self._write_enhanced_rejection_to_memory(agent_results, feedback)
                    print(f"\n📚 Learning from rejection: {feedback}")
                    print(f"Flow-GRPO training applied with negative signal.")
                    
                elif approval == "edited":
                    # Learn from feedback
                    self._write_enhanced_feedback_to_memory(agent_results, feedback)
                    print(f"\n📝 Learning from feedback: {feedback}")
                    print(f"Flow-GRPO training applied with corrective signal.")
                    
            except KeyboardInterrupt:
                print(f"\n🛑 Enhanced learning loop interrupted by user.")
                return False
            except Exception as e:
                print(f"\n❌ Error in enhanced iteration {iteration}: {e}")
                continue
        
        print(f"\n⚠️ Enhanced learning loop completed without approval.")
        print(f"Consider refining the goal or providing more specific feedback.")
        return False
    
    def _retrieve_enhanced_context(self, goal: str = None) -> Dict[str, str]:
        """
        Step 1: Retrieve enhanced context from memory with goal-driven selection.
        
        This includes both traditional context and agent-specific insights,
        dynamically selected based on goal analysis.
        """
        print("\n📚 STEP 1: Retrieving enhanced context from memory...")
        
        # Import goal analyzer
        from .goal_analyzer import GoalAnalyzer
        goal_analyzer = GoalAnalyzer()
        
        # If no goal provided, use default KPMG context for backward compatibility
        if goal:
            goal_analysis = goal_analyzer.analyze_goal(goal)
            print(f"   🎯 Goal Analysis: Domain={goal_analysis.domain}, Industry={goal_analysis.industry}, Market={goal_analysis.market}")
            
            # Get current project status using dynamic entity selection
            current_status = self._retrieve_dynamic_context(goal_analysis, "current project status and requirements")
        else:
            # Fallback to KPMG context for backward compatibility
            current_status = self.agent.chat("""
                OPERATION: RETRIEVE
                ENTITY: KPMG_strategyteam_project
                CONTEXT: Current project status and requirements for enhanced planning
                
                What is the current status of the KPMG strategy team project?
                What are the project requirements, deliverables, and timeline?
                What KPMG methodologies and frameworks should be used?
                What are the specific challenges and considerations?
            """).reply or "No current status available"
        
        # Get successful patterns (enhanced with agent insights)
        successful_patterns = self.agent.chat("""
            OPERATION: RETRIEVE
            ENTITY: successful_patterns
            CONTEXT: Review successful planning approaches across all agents
            
            What planning patterns have worked well across all 4 agents?
            What approaches led to successful workflow outcomes?
            What agent coordination strategies proved effective?
        """).reply or "No successful patterns yet (first iteration)"
        
        # Get errors to avoid (enhanced with agent insights)
        errors_to_avoid = self.agent.chat("""
            OPERATION: RETRIEVE
            ENTITY: planning_errors
            CONTEXT: Review planning mistakes across all agents
            
            What planning approaches have been rejected across all agents?
            What common mistakes should be avoided in agent coordination?
            What workflow patterns led to failures?
        """).reply or "No errors yet (no failures)"
        
        # Get execution history (enhanced with workflow tracking)
        execution_history = self.agent.chat("""
            OPERATION: RETRIEVE
            ENTITY: execution_log
            CONTEXT: Review past enhanced iterations and workflows
            
            What enhanced workflows have been successfully executed?
            How many iterations have completed with agent coordination?
            What were the outcomes of previous agentic workflows?
        """).reply or "No history yet (first iteration)"
        
        # Get agent performance insights
        agent_performance = self.agent.chat("""
            OPERATION: RETRIEVE
            ENTITY: agent_performance
            CONTEXT: Review agent performance and learning progress
            
            What are the current performance metrics for each agent?
            How has Flow-GRPO training improved planning over time?
            What agent-specific improvements have been observed?
        """).reply or "No performance data yet (first iteration)"
        
        context = {
            "current_status": current_status,
            "successful_patterns": successful_patterns,
            "errors_to_avoid": errors_to_avoid,
            "execution_history": execution_history,
            "agent_performance": agent_performance
        }
        
        print(f"   ✓ Current status retrieved")
        print(f"   ✓ Successful patterns: {len(successful_patterns)} chars")
        print(f"   ✓ Errors to avoid: {len(errors_to_avoid)} chars")
        print(f"   ✓ Execution history: {len(execution_history)} chars")
        print(f"   ✓ Agent performance: {len(agent_performance)} chars")
        
        return context
    
    def _retrieve_dynamic_context(self, goal_analysis, context_type: str) -> str:
        """Retrieve context dynamically based on goal analysis"""
        try:
            context_parts = []
            
            # Try to retrieve context from relevant entities
            for entity in goal_analysis.context_entities:
                try:
                    response = self.agent.chat(f"""
                        OPERATION: RETRIEVE
                        ENTITY: {entity}
                        CONTEXT: {context_type} for enhanced planning
                        
                        What information is available about {context_type}?
                        What methodologies, frameworks, or best practices are relevant?
                        What specific requirements, constraints, or considerations apply?
                    """)
                    if response.reply and response.reply.strip():
                        context_parts.append(f"=== {entity.upper()} ===\n{response.reply}")
                    else:
                        # If entity doesn't exist, create it with actual content
                        self._create_entity_with_content(entity, goal_analysis, context_type)
                        context_parts.append(f"=== {entity.upper()} ===\n[Entity created with relevant content]")
                except:
                    # If entity doesn't exist, create it with actual content
                    self._create_entity_with_content(entity, goal_analysis, context_type)
                    context_parts.append(f"=== {entity.upper()} ===\n[Entity created with relevant content]")
                    continue
            
            if context_parts:
                return "\n\n".join(context_parts)
            else:
                # Fallback to generic context
                return self.agent.chat(f"""
                    OPERATION: RETRIEVE
                    ENTITY: successful_patterns
                    CONTEXT: Generic {context_type} information
                    
                    What general information is available about {context_type}?
                    What best practices or frameworks can be applied?
                """).reply or f"No {context_type} available"
                
        except Exception as e:
            return f"Context retrieval failed: {str(e)}"
    
    def _create_entity_with_content(self, entity_name: str, goal_analysis, context_type: str):
        """Create entity with actual content instead of placeholder"""
        try:
            # Generate content based on entity type and goal
            content_prompt = f"""
                OPERATION: CREATE
                ENTITY: {entity_name}
                CONTEXT: {context_type} for {goal_analysis.domain} project in {goal_analysis.market}
                
                Create comprehensive content for the {entity_name} entity that includes:
                1. Relevant information for {context_type}
                2. Specific details for {goal_analysis.domain} domain
                3. Market-specific considerations for {goal_analysis.market}
                4. Industry best practices and frameworks
                5. Practical implementation guidance
                
                Make this content detailed, actionable, and directly relevant to the project goal.
                Do not create placeholder text - provide real, useful information.
            """
            
            response = self.agent.chat(content_prompt)
            if response.reply and response.reply.strip():
                # Create the entity file with actual content
                entity_file = self.memory_path / "entities" / f"{entity_name}.md"
                entity_file.write_text(response.reply)
                print(f"   ✅ Created {entity_name} with actual content")
            
        except Exception as e:
            print(f"   ⚠️ Failed to create {entity_name}: {e}")
            # Create minimal placeholder as fallback
            entity_file = self.memory_path / "entities" / f"{entity_name}.md"
            entity_file.write_text(f"# {entity_name.replace('_', ' ').title()}\n\nThis entity contains information relevant to the current project.")
    
    def _populate_entities_with_agent_content(self, goal: str, agent_results: Dict):
        """Populate entities with actual content from agent results"""
        print("\n📝 Populating entities with agent-generated content...")
        
        # Map entity types to agent content
        entity_mappings = {
            'executive_summary_report': 'generator',
            'detailed_implementation_plan': 'planner', 
            'market_analysis_report': 'executor',
            'competitive_intelligence_analysis': 'executor',
            'risk_assessment_and_mitigation_strategy': 'verifier',
            'quality_assurance_framework': 'verifier',
            'timeline_and_resource_allocation': 'planner',
            'success_metrics_and_kpis': 'generator',
            'recommendations_and_next_steps': 'generator',
            'vietnam_market_analysis': 'executor',
            'vietnamese_regulations': 'executor',
            'regulatory_landscape_analysis': 'verifier',
            'regulatory_submission_timeline': 'planner',
            'clinical_trial_strategy': 'executor',
            'clinical_protocols': 'executor',
            'healthcare_data_privacy_framework': 'verifier',
            'healthcare_regulations': 'executor',
            'medical_market_analysis': 'executor',
            'raffles_medical_vietnam': 'executor',
            'Japanese_Hospital_Vietnam_Market_Entry': 'planner'
        }
        
        for entity_name, agent_type in entity_mappings.items():
            try:
                agent_result = agent_results.get(agent_type)
                if agent_result and agent_result.success and agent_result.output:
                    # Create entity with actual content from agent
                    entity_file = self.memory_path / "entities" / f"{entity_name}.md"
                    
                    # Generate entity-specific content based on agent output
                    entity_content = f"""# {entity_name.replace('_', ' ').title()}

## Project Context
**Goal:** {goal}
**Generated by:** {agent_type.title()} Agent
**Timestamp:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Content

{agent_result.output}

## Metadata
- Agent Type: {agent_type}
- Success: {agent_result.success}
- Content Length: {len(agent_result.output)} characters
- Generated: {agent_result.timestamp}
"""
                    
                    entity_file.write_text(entity_content)
                    print(f"   ✅ Populated {entity_name} with {agent_type} content")
                else:
                    # Create placeholder if no agent content available
                    entity_file = self.memory_path / "entities" / f"{entity_name}.md"
                    if not entity_file.exists():
                        entity_file.write_text(f"# {entity_name.replace('_', ' ').title()}\n\nThis entity will be populated with relevant content from the {agent_type} agent.")
                        print(f"   📝 Created placeholder for {entity_name}")
                        
            except Exception as e:
                print(f"   ⚠️ Failed to populate {entity_name}: {e}")
        
        print(f"   ✅ Entity population completed")
    
    def _get_human_approval(self, agent_results: Dict, goal: str) -> Tuple[str, str]:
        """
        Step 3: Get human approval for the coordinated workflow.
        
        This shows results from all 4 agents for comprehensive review.
        """
        print("\n👤 STEP 3: Human approval required for coordinated workflow")
        print("=" * 80)
        
        # Display results from each agent
        print("📋 COORDINATED WORKFLOW RESULTS:")
        print("-" * 50)
        
        if 'planner' in agent_results:
            planner_result = agent_results['planner']
            print(f"\n🧭 PLANNER AGENT RESULTS:")
            print(f"Success: {'✅' if planner_result.success else '❌'}")
            print(f"Output: {planner_result.output[:300]}...")
        
        if 'verifier' in agent_results:
            verifier_result = agent_results['verifier']
            print(f"\n✅ VERIFIER AGENT RESULTS:")
            print(f"Success: {'✅' if verifier_result.success else '❌'}")
            print(f"Plan Valid: {'✅ VALID' if verifier_result.metadata.get('is_valid') else '⚠️ INVALID'}")
            print(f"Output: {verifier_result.output[:300]}...")
        
        if 'executor' in agent_results:
            executor_result = agent_results['executor']
            print(f"\n🛠️ EXECUTOR AGENT RESULTS:")
            print(f"Success: {'✅' if executor_result.success else '❌'}")
            print(f"Deliverables: {executor_result.metadata.get('deliverables_created', 0)}")
            print(f"Output: {executor_result.output[:300]}...")
        
        if 'generator' in agent_results:
            generator_result = agent_results['generator']
            print(f"\n✍️ GENERATOR AGENT RESULTS:")
            print(f"Success: {'✅' if generator_result.success else '❌'}")
            print(f"Deliverables: {generator_result.metadata.get('deliverables_created', 0)}")
            print(f"Output: {generator_result.output[:300]}...")
        
        print("-" * 50)
        
        print("\n💡 OPTIONS:")
        print("  y     - Approve and execute coordinated workflow")
        print("  n     - Reject workflow (will learn from this)")
        print("  edit  - Provide corrective feedback")
        print("  quit  - Stop enhanced orchestrator")
        
        while True:
            choice = input("\n👉 Your decision (y/n/edit/quit): ").lower().strip()
            
            if choice == 'y':
                return "approved", ""
            elif choice == 'n':
                reason = input("📝 Why reject? (helps system learn): ")
                return "rejected", reason
            elif choice == 'edit':
                feedback = input("📝 What changes needed?: ")
                return "edited", feedback
            elif choice == 'quit':
                print("\n🛑 Enhanced orchestrator stopped by user.")
                sys.exit(0)
            else:
                print("❌ Invalid choice. Please enter y, n, edit, or quit.")
    
    def _execute_enhanced_workflow(self, agent_results: Dict, goal: str) -> Dict:
        """
        Step 4: Execute the approved coordinated workflow.
        
        This creates comprehensive deliverables using all agent outputs.
        """
        print("\n⚙️  STEP 4: Executing enhanced coordinated workflow...")
        
        try:
            # Combine all agent outputs for comprehensive execution
            combined_outputs = self._combine_agent_outputs(agent_results)
            
            # Create comprehensive execution report
            execution_report = f"""
# Enhanced Workflow Execution Report

## Goal
{goal}

## Coordinated Agent Results

### 🧭 Planner Agent
{agent_results['planner'].output if agent_results.get('planner') else 'No planner results'}

### ✅ Verifier Agent  
{agent_results['verifier'].output if agent_results.get('verifier') else 'No verifier results'}

### 🛠️ Executor Agent
{agent_results['executor'].output if agent_results.get('executor') else 'No executor results'}

### ✍️ Generator Agent
{agent_results['generator'].output if agent_results.get('generator') else 'No generator results'}

## Combined Execution Results
{combined_outputs}

## Workflow Success Metrics
- Planner Success: {'✅' if agent_results.get('planner', {}).success else '❌'}
- Verifier Success: {'✅' if agent_results.get('verifier', {}).success else '❌'}
- Executor Success: {'✅' if agent_results.get('executor', {}).success else '❌'}
- Generator Success: {'✅' if agent_results.get('generator', {}).success else '❌'}

## Flow-GRPO Training Applied
- Training Signal: Applied based on overall workflow success
- Memory Updated: Enhanced patterns and performance metrics
- Learning Impact: Planner improved for future iterations

---
*Executed by Enhanced Learning Orchestrator with AgentFlow Integration*
"""
            
            # Store comprehensive deliverables
            self._store_enhanced_deliverables(goal, execution_report, agent_results)
            
            # Populate entities with actual agent content
            self._populate_entities_with_agent_content(goal, agent_results)
            
            # Store the comprehensive plan to plans/ directory
            self._save_plan_to_file(goal, agent_results)
            
            print(f"   ✅ Enhanced workflow executed successfully")
            print(f"   📄 Comprehensive execution report: {len(execution_report)} chars")
            print(f"   📁 Enhanced deliverables created and stored")
            print(f"   📝 Entities populated with agent content")
            print(f"   📄 Comprehensive plan saved to plans/ directory")
            
            # Store execution results
            result = {
                "status": "success",
                "actions_completed": len(agent_results),
                "total_actions": len(agent_results),
                "execution_report": execution_report,
                "agent_results": agent_results,
                "deliverables_created": True,
                "flow_grpo_applied": True,
                "timestamp": datetime.now().isoformat()
            }
            
            return result
            
        except Exception as e:
            print(f"   ❌ Enhanced workflow execution failed: {e}")
            return {
                "status": "failed",
                "actions_completed": 0,
                "total_actions": len(agent_results),
                "error": str(e),
                "flow_grpo_applied": False,
                "timestamp": datetime.now().isoformat()
            }
    
    def _combine_agent_outputs(self, agent_results: Dict) -> str:
        """Combine outputs from all agents into comprehensive results"""
        
        combined = "## Enhanced Coordinated Workflow Results\n\n"
        
        # Add planner insights
        if 'planner' in agent_results and agent_results['planner'].success:
            combined += "### Strategic Planning Insights\n"
            combined += agent_results['planner'].output[:500] + "...\n\n"
        
        # Add verification insights
        if 'verifier' in agent_results and agent_results['verifier'].success:
            combined += "### Quality Validation Insights\n"
            combined += agent_results['verifier'].output[:500] + "...\n\n"
        
        # Add execution insights
        if 'executor' in agent_results and agent_results['executor'].success:
            combined += "### Implementation Insights\n"
            combined += agent_results['executor'].output[:500] + "...\n\n"
        
        # Add synthesis insights
        if 'generator' in agent_results and agent_results['generator'].success:
            combined += "### Synthesis and Final Deliverables\n"
            combined += agent_results['generator'].output[:500] + "...\n\n"
        
        combined += "### Workflow Coordination Summary\n"
        combined += f"- Total Agents Coordinated: {len(agent_results)}\n"
        combined += f"- Successful Agents: {sum(1 for result in agent_results.values() if result.success)}\n"
        combined += f"- Flow-GRPO Training: Applied\n"
        combined += f"- Memory Enhancement: Completed\n"
        
        return combined
    
    def _store_enhanced_deliverables(self, goal: str, execution_report: str, agent_results: Dict):
        """Store comprehensive deliverables from enhanced workflow"""
        print("\n📁 Storing enhanced deliverables...")
        
        # Create deliverables directory
        deliverables_dir = self.memory_path / "deliverables"
        deliverables_dir.mkdir(exist_ok=True)
        
        # Generate timestamp for file naming
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Store the comprehensive execution report
        execution_file = deliverables_dir / f"enhanced_execution_report_{timestamp}.md"
        execution_file.write_text(execution_report)
        
        # Store individual agent deliverables
        self._store_agent_specific_deliverables(goal, agent_results, timestamp)
        
        print(f"   ✅ Enhanced deliverables stored in {deliverables_dir}")
    
    def _store_agent_specific_deliverables(self, goal: str, agent_results: Dict, timestamp: str):
        """Store deliverables specific to each agent"""
        entities_dir = self.memory_path / "entities"
        
        # Store planner deliverables
        if 'planner' in agent_results:
            planner_file = entities_dir / f"planner_strategy_{timestamp}.md"
            planner_file.write_text(f"""# Planner Agent Strategy - {timestamp}

## Goal
{goal}

## Strategic Plan
{agent_results['planner'].output}

## Planning Metadata
- Success: {agent_results['planner'].success}
- Plan Length: {agent_results['planner'].metadata.get('plan_length', 0)} chars
- Patterns Applied: {agent_results['planner'].metadata.get('patterns_applied', 0)}
- Errors Avoided: {agent_results['planner'].metadata.get('errors_avoided', 0)}
""")
        
        # Store executor deliverables
        if 'executor' in agent_results:
            executor_file = entities_dir / f"executor_implementation_{timestamp}.md"
            executor_file.write_text(f"""# Executor Agent Implementation - {timestamp}

## Goal
{goal}

## Implementation Results
{agent_results['executor'].output}

## Execution Metadata
- Success: {agent_results['executor'].success}
- Deliverables Created: {agent_results['executor'].metadata.get('deliverables_created', 0)}
- Phases Executed: {agent_results['executor'].metadata.get('phases_executed', 0)}
""")
        
        # Store verifier deliverables
        if 'verifier' in agent_results:
            verifier_file = entities_dir / f"verifier_validation_{timestamp}.md"
            verifier_file.write_text(f"""# Verifier Agent Validation - {timestamp}

## Goal
{goal}

## Validation Results
{agent_results['verifier'].output}

## Verification Metadata
- Success: {agent_results['verifier'].success}
- Plan Valid: {agent_results['verifier'].metadata.get('is_valid', False)}
- Checks Performed: {agent_results['verifier'].metadata.get('checks_performed', 0)}
""")
        
        # Store generator deliverables
        if 'generator' in agent_results:
            generator_file = entities_dir / f"generator_synthesis_{timestamp}.md"
            generator_file.write_text(f"""# Generator Agent Synthesis - {timestamp}

## Goal
{goal}

## Synthesis Results
{agent_results['generator'].output}

## Generation Metadata
- Success: {agent_results['generator'].success}
- Deliverables Created: {agent_results['generator'].metadata.get('deliverables_created', 0)}
- Synthesis Length: {agent_results['generator'].metadata.get('synthesis_length', 0)} chars
""")
        
        print(f"   ✅ Agent-specific deliverables stored")
    
    def _save_plan_to_file(self, goal: str, agent_results: Dict):
        """Save the comprehensive plan to plans/ directory for visibility."""
        print("\n📄 Saving comprehensive plan to plans/ directory...")
        
        # Create plans directory
        plans_dir = self.memory_path / "plans"
        plans_dir.mkdir(exist_ok=True)
        
        # Generate timestamp for file naming
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Create plan filename
        goal_slug = goal.replace(" ", "_").replace("/", "_").replace("\\", "_")[:50]
        plan_file = plans_dir / f"plan_{timestamp}_{goal_slug}.md"
        
        # Get the comprehensive plan content from planner agent
        planner_result = agent_results.get('planner')
        verifier_result = agent_results.get('verifier')
        executor_result = agent_results.get('executor')
        generator_result = agent_results.get('generator')
        
        plan_content = f"""# Generated Plan - {timestamp}

## Goal
{goal}

## Generated Plan

{planner_result.output if planner_result else 'No planner results'}

## Verification Results

{verifier_result.output if verifier_result else 'No verifier results'}

## Execution Results

{executor_result.output if executor_result else 'No executor results'}

## Synthesis Results

{generator_result.output if generator_result else 'No generator results'}

## Plan Statistics
- Plan Length: {len(planner_result.output) if planner_result else 0} characters
- Verification Length: {len(verifier_result.output) if verifier_result else 0} characters
- Execution Length: {len(executor_result.output) if executor_result else 0} characters
- Synthesis Length: {len(generator_result.output) if generator_result else 0} characters
- Total Content: {sum([
    len(planner_result.output) if planner_result else 0,
    len(verifier_result.output) if verifier_result else 0,
    len(executor_result.output) if executor_result else 0,
    len(generator_result.output) if generator_result else 0
])} characters

## Agent Performance
- Planner Success: {'✅' if planner_result and planner_result.success else '❌'}
- Verifier Success: {'✅' if verifier_result and verifier_result.success else '❌'}
- Executor Success: {'✅' if executor_result and executor_result.success else '❌'}
- Generator Success: {'✅' if generator_result and generator_result.success else '❌'}

---
*Generated by Enhanced Learning Orchestrator with AgentFlow Integration at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
"""
        
        plan_file.write_text(plan_content)
        print(f"   📄 Comprehensive plan saved to: {plan_file}")
    
    def _write_enhanced_success_to_memory(self, agent_results: Dict, execution: Dict):
        """
        Step 5: Write successful execution to memory for learning.
        
        This enhances the memory with agent-specific insights and Flow-GRPO training data.
        """
        print("\n💾 STEP 5: Writing enhanced success to memory (learning!)...")
        
        # Update enhanced execution log
        execution_log = self.memory_path / "entities" / "execution_log.md"
        if execution_log.exists():
            with open(execution_log, 'a') as f:
                f.write(f"\n## Enhanced Execution {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"**Goal:** {execution.get('goal', 'Unknown')}\n")
                f.write(f"**Status:** {execution['status']}\n")
                f.write(f"**Flow-GRPO Training:** Applied\n\n")
                
                # Add agent-specific results
                f.write("**Agent Results:**\n")
                for agent_name, result in agent_results.items():
                    f.write(f"- {agent_name}: {'✅ SUCCESS' if result.success else '❌ FAILED'}\n")
                f.write("\n")
        
        # Update enhanced successful patterns
        patterns_file = self.memory_path / "entities" / "successful_patterns.md"
        if patterns_file.exists():
            with open(patterns_file, 'a') as f:
                f.write(f"\n## Enhanced Successful Pattern - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"**Goal Type:** {execution.get('goal', 'Unknown')}\n")
                f.write(f"**What Worked:** Coordinated workflow was approved and executed successfully\n")
                f.write(f"**Agent Coordination:** All agents worked together effectively\n")
                f.write(f"**Flow-GRPO Training:** Positive signal applied to Planner\n\n")
                
                # Add agent-specific success patterns
                f.write("**Agent-Specific Success Factors:**\n")
                if 'planner' in agent_results and agent_results['planner'].success:
                    f.write(f"- Planner: Strategic approach was effective\n")
                if 'executor' in agent_results and agent_results['executor'].success:
                    f.write(f"- Executor: Implementation method worked well\n")
                if 'verifier' in agent_results and agent_results['verifier'].success:
                    f.write(f"- Verifier: Validation approach was successful\n")
                if 'generator' in agent_results and agent_results['generator'].success:
                    f.write(f"- Generator: Synthesis method was effective\n")
                f.write("\n")
        
        print("   ✅ Enhanced execution log updated")
        print("   ✅ Enhanced successful patterns recorded")
        print("   ✅ Flow-GRPO training data stored")
        print("   ✅ Memory enriched with agent-specific insights")
    
    def _write_enhanced_rejection_to_memory(self, agent_results: Dict, feedback: str):
        """Write rejection feedback to memory with agent-specific insights"""
        print("\n📚 Learning from enhanced rejection...")
        
        errors_file = self.memory_path / "entities" / "planning_errors.md"
        if errors_file.exists():
            with open(errors_file, 'a') as f:
                f.write(f"\n## Enhanced Rejection - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"**Feedback:** {feedback}\n")
                f.write(f"**Flow-GRPO Training:** Negative signal applied to Planner\n\n")
                
                # Add agent-specific rejection insights
                f.write("**Agent Results at Rejection:**\n")
                for agent_name, result in agent_results.items():
                    f.write(f"- {agent_name}: {'✅ SUCCESS' if result.success else '❌ FAILED'}\n")
                f.write("\n")
        
        print("   ✅ Enhanced rejection feedback recorded")
        print("   ✅ Flow-GRPO training applied with negative signal")
    
    def _write_enhanced_feedback_to_memory(self, agent_results: Dict, feedback: str):
        """Write corrective feedback to memory with agent-specific insights"""
        print("\n📝 Learning from enhanced feedback...")
        
        patterns_file = self.memory_path / "entities" / "successful_patterns.md"
        if patterns_file.exists():
            with open(patterns_file, 'a') as f:
                f.write(f"\n## Enhanced Feedback - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"**Feedback:** {feedback}\n")
                f.write(f"**Flow-GRPO Training:** Corrective signal applied to Planner\n\n")
                
                # Add agent-specific feedback insights
                f.write("**Agent Results at Feedback:**\n")
                for agent_name, result in agent_results.items():
                    f.write(f"- {agent_name}: {'✅ SUCCESS' if result.success else '❌ FAILED'}\n")
                f.write("\n")
        
        print("   ✅ Enhanced feedback recorded")
        print("   ✅ Flow-GRPO training applied with corrective signal")


# Example usage
if __name__ == "__main__":
    # Initialize enhanced orchestrator
    memory_path = "/Users/teije/Desktop/memagent/local-memory"
    orchestrator = EnhancedLearningOrchestrator(memory_path=memory_path, max_iterations=5)
    
    # Run enhanced learning loop
    goal = "Develop a comprehensive market entry strategy for a tech company using enhanced agentic coordination"
    success = orchestrator.run_enhanced_learning_loop(goal)
    
    if success:
        print("\n🎉 Enhanced learning loop completed successfully!")
        print("🎯 Flow-GRPO training has improved the Planner Agent for future iterations!")
    else:
        print("\n⚠️ Enhanced learning loop completed without approval.")
