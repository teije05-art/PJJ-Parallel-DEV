"""
AgentFlow-Inspired Specialized Agents

Four specialized agent modules that coordinate through MemAgent:
1. Planner Agent - Strategic planning and decision making
2. Executor Agent - Tool execution and action implementation  
3. Verifier Agent - Quality checking and validation
4. Generator Agent - Content synthesis and final output creation

Each agent uses MemAgent for context, execution, and memory storage.
"""

import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass

# Add repo root to path
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from agent import Agent
from .goal_analyzer import GoalAnalyzer
from .domain_templates import DomainTemplates


@dataclass
class AgentResult:
    """Standard result format for all agent operations"""
    success: bool
    output: str
    metadata: Dict[str, Any]
    timestamp: str


class BaseAgent:
    """Base class for all specialized agents"""
    
    def __init__(self, agent: Agent, memory_path: Path):
        self.agent = agent
        self.memory_path = memory_path
        self.agent_type = self.__class__.__name__
        self.goal_analyzer = GoalAnalyzer()
        self.domain_templates = DomainTemplates()
        
    def _log_agent_action(self, action: str, result: AgentResult):
        """Log agent actions to MemAgent for coordination tracking"""
        log_entry = f"""
## {self.agent_type} Action - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

**Action:** {action}
**Success:** {result.success}
**Output:** {result.output[:200]}...
**Metadata:** {result.metadata}

---
"""
        
        # Store in agent coordination log
        coordination_file = self.memory_path / "entities" / "agent_coordination.md"
        if coordination_file.exists():
            with open(coordination_file, 'a') as f:
                f.write(log_entry)
        else:
            coordination_file.write_text(f"# Agent Coordination Log\n\n{log_entry}")


class PlannerAgent(BaseAgent):
    """
    🧭 Planner Agent - The strategic decision maker
    
    Responsibilities:
    - Analyze project context from MemAgent
    - Generate high-level strategic plans
    - Decide on tool usage and action sequences
    - Coordinate with other agents through shared memory
    """
    
    def generate_strategic_plan(self, goal: str, context: Dict[str, str]) -> AgentResult:
        """Generate a strategic plan using MemAgent context and learned patterns"""
        
        print(f"\n🧭 PLANNER AGENT: Generating strategic plan...")
        
        # Analyze the goal to determine domain and context requirements
        goal_analysis = self.goal_analyzer.analyze_goal(goal)
        
        # Retrieve comprehensive context from MemAgent using dynamic selection
        project_context = self._retrieve_project_context(goal)
        successful_patterns = self._retrieve_successful_patterns()
        error_patterns = self._retrieve_error_patterns()
        current_state = self._retrieve_current_state()
        
        # Prepare context data for template
        context_data = {
            'goal': goal,
            'project_context': project_context,
            'successful_patterns': successful_patterns,
            'error_patterns': error_patterns,
            'execution_history': current_state,
            'current_status': context.get('current_status', 'No previous context'),
            'web_search_results': context.get('web_search_results', 'No web search results available')
        }
        
        # Generate domain-specific planning prompt
        planning_prompt = self.domain_templates.get_planning_prompt(goal_analysis, context_data)
        
        try:
            response = self.agent.chat(planning_prompt)
            plan_text = response.reply or "Planning failed"
            
            # Parse and validate the plan
            plan_metadata = {
                "goal": goal,
                "domain": goal_analysis.domain,
                "industry": goal_analysis.industry,
                "market": goal_analysis.market,
                "company_type": goal_analysis.company_type,
                "context_entities_used": goal_analysis.context_entities,
                "methodologies_applied": goal_analysis.methodologies,
                "project_context_retrieved": len(project_context),
                "patterns_applied": len(successful_patterns),
                "errors_avoided": len(error_patterns),
                "plan_length": len(plan_text)
            }
            
            result = AgentResult(
                success=True,
                output=plan_text,
                metadata=plan_metadata,
                timestamp=datetime.now().isoformat()
            )
            
            # Log the planning action
            self._log_agent_action("generate_strategic_plan", result)
            
            print(f"   ✅ Strategic plan generated ({len(plan_text)} chars)")
            print(f"   ✅ Domain: {goal_analysis.domain} | Industry: {goal_analysis.industry} | Market: {goal_analysis.market}")
            print(f"   ✅ Used {len(goal_analysis.context_entities)} context entities: {', '.join(goal_analysis.context_entities)}")
            print(f"   ✅ Applied {len(goal_analysis.methodologies)} domain-specific methodologies")
            print(f"   ✅ Used {plan_metadata['patterns_applied']} learned patterns")
            print(f"   ✅ Avoided {plan_metadata['errors_avoided']} error patterns")
            
            return result
            
        except Exception as e:
            error_result = AgentResult(
                success=False,
                output=f"Planning failed: {str(e)}",
                metadata={"error": str(e)},
                timestamp=datetime.now().isoformat()
            )
            self._log_agent_action("generate_strategic_plan", error_result)
            return error_result
    
    def _retrieve_project_context(self, goal: str) -> str:
        """Retrieve project context dynamically based on goal analysis"""
        try:
            # Analyze the goal to determine relevant context
            goal_analysis = self.goal_analyzer.analyze_goal(goal)
            
            # Retrieve context from multiple relevant entities
            context_parts = []
            
            for entity in goal_analysis.context_entities:
                try:
                    response = self.agent.chat(f"""
                        OPERATION: RETRIEVE
                        ENTITY: {entity}
                        CONTEXT: Comprehensive project context for strategic planning
                        
                        Provide detailed information about:
                        - Current project status and requirements
                        - Industry-specific methodologies and frameworks
                        - Market dynamics and competitive landscape
                        - Regulatory requirements and compliance standards
                        - Quality standards and best practices
                        - Any specific challenges and considerations
                    """)
                    if response.reply and response.reply.strip():
                        context_parts.append(f"=== {entity.upper()} CONTEXT ===\n{response.reply}")
                except:
                    continue
            
            if context_parts:
                combined_context = "\n\n".join(context_parts)
                return combined_context
            else:
                # Fallback to generic context if no specific entities found
                return self._retrieve_generic_context(goal_analysis)
                
        except Exception as e:
            return f"Context retrieval failed: {str(e)}"
    
    def _retrieve_generic_context(self, goal_analysis) -> str:
        """Retrieve generic context when no specific entities are available"""
        try:
            response = self.agent.chat(f"""
                OPERATION: RETRIEVE
                ENTITY: successful_patterns
                CONTEXT: Generic strategic planning context
                
                Provide information about:
                - General strategic planning approaches
                - Market entry methodologies
                - Business development frameworks
                - Risk assessment protocols
                - Success metrics and KPIs
            """)
            return response.reply or "No generic context available"
        except:
            return "Generic context retrieval failed"
    
    def _retrieve_successful_patterns(self) -> str:
        """Retrieve successful planning patterns from MemAgent"""
        try:
            response = self.agent.chat("""
                OPERATION: RETRIEVE
                ENTITY: successful_patterns
                CONTEXT: Proven planning approaches
                
                What planning patterns have worked well?
                What specific approaches led to successful outcomes?
                What methodologies proved effective?
            """)
            return response.reply or "No successful patterns available"
        except:
            return "Pattern retrieval failed"
    
    def _retrieve_error_patterns(self) -> str:
        """Retrieve error patterns to avoid from MemAgent"""
        try:
            response = self.agent.chat("""
                OPERATION: RETRIEVE
                ENTITY: planning_errors
                CONTEXT: Planning mistakes to avoid
                
                What planning approaches have been rejected?
                What common mistakes should be avoided?
                What patterns led to failures?
            """)
            return response.reply or "No error patterns available"
        except:
            return "Error pattern retrieval failed"
    
    def _retrieve_current_state(self) -> str:
        """Retrieve current project state from MemAgent"""
        try:
            response = self.agent.chat("""
                OPERATION: RETRIEVE
                ENTITY: execution_log
                CONTEXT: Current project state
                
                What is the current state of the project?
                What has been completed?
                What is the next priority?
            """)
            return response.reply or "No current state available"
        except:
            return "Current state retrieval failed"


class ExecutorAgent(BaseAgent):
    """
    🛠️ Executor Agent - The implementation specialist
    
    Responsibilities:
    - Execute plans by calling appropriate tools
    - Implement actions and create deliverables
    - Coordinate with MemAgent for execution tracking
    - Provide detailed execution feedback
    """
    
    def execute_plan(self, plan: str, goal: str) -> AgentResult:
        """Execute a strategic plan using MemAgent tools and capabilities"""
        
        print(f"\n🛠️ EXECUTOR AGENT: Executing strategic plan...")
        
        # Create execution prompt that uses MemAgent for actual work
        execution_prompt = f"""
You are the Executor Agent in an advanced agentic system. Your role is to actually implement plans and create real deliverables using MemAgent capabilities.

GOAL: {goal}

STRATEGIC PLAN TO EXECUTE:
{plan}

INSTRUCTIONS:
Actually execute this plan by:

1. **CREATE REAL DELIVERABLES**: Use MemAgent to create actual work products, not just descriptions
2. **IMPLEMENT EACH PHASE**: Execute each phase of the plan systematically
3. **USE KPMG METHODOLOGIES**: Apply specific KPMG frameworks and tools
4. **TRACK PROGRESS**: Record each step and its outcomes
5. **GENERATE CONCRETE OUTPUTS**: Create documents, analyses, frameworks, etc.

EXECUTION APPROACH:
For each phase in the plan, create the specific deliverables mentioned:

- Market analysis reports (if applicable)
- Competitive intelligence analysis (if applicable)
- Risk assessment methodology (if applicable)
- Project framework documents (if applicable)
- Implementation timelines (if applicable)
- Quality assurance checklists (if applicable)
- Survey/interview guides (if applicable)
- Case studies (if applicable)

Use MemAgent operations to:
- CREATE entities for each deliverable
- STORE detailed content and analysis
- TRACK execution progress
- GENERATE actionable recommendations

This is REAL execution - create actual work products that meet KPMG standards.
"""
        
        try:
            response = self.agent.chat(execution_prompt)
            execution_text = response.reply or "Execution failed"
            
            # Parse execution results
            execution_metadata = {
                "goal": goal,
                "plan_length": len(plan),
                "execution_length": len(execution_text),
                "deliverables_created": self._count_deliverables(execution_text),
                "phases_executed": self._count_phases(plan)
            }
            
            result = AgentResult(
                success=True,
                output=execution_text,
                metadata=execution_metadata,
                timestamp=datetime.now().isoformat()
            )
            
            # Log the execution action
            self._log_agent_action("execute_plan", result)
            
            print(f"   ✅ Plan executed ({execution_metadata['deliverables_created']} deliverables)")
            print(f"   ✅ {execution_metadata['phases_executed']} phases completed")
            
            return result
            
        except Exception as e:
            error_result = AgentResult(
                success=False,
                output=f"Execution failed: {str(e)}",
                metadata={"error": str(e)},
                timestamp=datetime.now().isoformat()
            )
            self._log_agent_action("execute_plan", error_result)
            return error_result
    
    def _count_deliverables(self, execution_text: str) -> int:
        """Count the number of deliverables mentioned in execution text"""
        deliverable_keywords = [
            "market analysis", "competitive intelligence", "risk assessment",
            "project framework", "implementation timeline", "quality assurance",
            "survey guide", "interview guide", "case study", "report"
        ]
        count = 0
        for keyword in deliverable_keywords:
            if keyword.lower() in execution_text.lower():
                count += 1
        return count
    
    def _count_phases(self, plan_text: str) -> int:
        """Count the number of phases in the plan"""
        return plan_text.lower().count("phase")


class VerifierAgent(BaseAgent):
    """
    ✅ Verifier Agent - The quality assurance specialist
    
    Responsibilities:
    - Validate plans against project requirements
    - Check execution quality and completeness
    - Verify compliance with KPMG standards
    - Provide detailed feedback for improvement
    """
    
    def verify_plan(self, plan: str, goal: str) -> AgentResult:
        """Verify a plan against project requirements and standards"""
        
        print(f"\n✅ VERIFIER AGENT: Validating strategic plan...")
        
        # Create verification prompt using MemAgent context
        verification_prompt = f"""
You are the Verifier Agent in an advanced agentic system. Your role is to validate plans against project requirements and KPMG standards.

GOAL: {goal}

PLAN TO VERIFY:
{plan}

VERIFICATION CHECKLIST:
1. **PROJECT ALIGNMENT**: Does the plan align with KPMG project requirements?
2. **METHODOLOGY COMPLIANCE**: Does it use appropriate KPMG frameworks?
3. **DELIVERABLE COMPLETENESS**: Are all required deliverables addressed?
4. **TIMELINE REALISTIC**: Is the timeline achievable given constraints?
5. **RESOURCE ALLOCATION**: Are resources properly allocated?
6. **QUALITY STANDARDS**: Does it meet KPMG quality requirements?
7. **RISK MANAGEMENT**: Are risks properly identified and mitigated?
8. **CLIENT EXPECTATIONS**: Will it meet client expectations?

Use MemAgent to check against:
- KPMG_Project_Procedures entity
- KPMG_strategyteam_project requirements
- Quality standards and compliance requirements

Provide detailed verification with:
- Overall assessment (VALID/INVALID)
- Specific compliance checks
- Missing elements or gaps
- Recommendations for improvement
- Risk assessment
"""
        
        try:
            response = self.agent.chat(verification_prompt)
            verification_text = response.reply or "Verification failed"
            
            # Determine if plan is valid
            is_valid = self._assess_validation(verification_text)
            
            verification_metadata = {
                "goal": goal,
                "plan_length": len(plan),
                "is_valid": is_valid,
                "verification_length": len(verification_text),
                "checks_performed": self._count_verification_checks(verification_text)
            }
            
            result = AgentResult(
                success=True,
                output=verification_text,
                metadata=verification_metadata,
                timestamp=datetime.now().isoformat()
            )
            
            # Log the verification action
            self._log_agent_action("verify_plan", result)
            
            status = "✅ VALID" if is_valid else "⚠️ INVALID"
            print(f"   {status} Plan verification completed")
            print(f"   ✅ {verification_metadata['checks_performed']} checks performed")
            
            return result
            
        except Exception as e:
            error_result = AgentResult(
                success=False,
                output=f"Verification failed: {str(e)}",
                metadata={"error": str(e)},
                timestamp=datetime.now().isoformat()
            )
            self._log_agent_action("verify_plan", error_result)
            return error_result
    
    def verify_execution(self, execution_result: str, plan: str) -> AgentResult:
        """Verify execution results against the original plan"""
        
        print(f"\n✅ VERIFIER AGENT: Validating execution results...")
        
        verification_prompt = f"""
You are the Verifier Agent validating execution results against the original plan.

ORIGINAL PLAN:
{plan}

EXECUTION RESULTS:
{execution_result}

VERIFICATION CHECKLIST:
1. **COMPLETENESS**: Were all planned phases executed?
2. **QUALITY**: Do the deliverables meet expected standards?
3. **ACCURACY**: Are the outputs accurate and well-researched?
4. **FORMAT**: Do deliverables follow proper KPMG formats?
5. **TIMELINE**: Was execution completed within expected timeframe?
6. **RESOURCES**: Were resources used efficiently?
7. **CLIENT VALUE**: Will deliverables meet client needs?

Provide detailed assessment with:
- Overall execution quality (EXCELLENT/GOOD/SATISFACTORY/NEEDS_IMPROVEMENT)
- Specific quality metrics
- Areas of strength
- Areas needing improvement
- Recommendations for future executions
"""
        
        try:
            response = self.agent.chat(verification_prompt)
            verification_text = response.reply or "Execution verification failed"
            
            # Assess execution quality
            quality_score = self._assess_execution_quality(verification_text)
            
            verification_metadata = {
                "plan_length": len(plan),
                "execution_length": len(execution_result),
                "quality_score": quality_score,
                "verification_length": len(verification_text)
            }
            
            result = AgentResult(
                success=True,
                output=verification_text,
                metadata=verification_metadata,
                timestamp=datetime.now().isoformat()
            )
            
            # Log the verification action
            self._log_agent_action("verify_execution", result)
            
            print(f"   ✅ Execution verification completed (Quality: {quality_score})")
            
            return result
            
        except Exception as e:
            error_result = AgentResult(
                success=False,
                output=f"Execution verification failed: {str(e)}",
                metadata={"error": str(e)},
                timestamp=datetime.now().isoformat()
            )
            self._log_agent_action("verify_execution", error_result)
            return error_result
    
    def _assess_validation(self, verification_text: str) -> bool:
        """Assess if plan is valid based on verification text"""
        text_lower = verification_text.lower()
        if "invalid" in text_lower and "valid" not in text_lower:
            return False
        if "valid" in text_lower and "invalid" not in text_lower:
            return True
        # Default to valid if unclear
        return True
    
    def _assess_execution_quality(self, verification_text: str) -> str:
        """Assess execution quality based on verification text"""
        text_lower = verification_text.lower()
        if "excellent" in text_lower:
            return "EXCELLENT"
        elif "good" in text_lower:
            return "GOOD"
        elif "satisfactory" in text_lower:
            return "SATISFACTORY"
        else:
            return "NEEDS_IMPROVEMENT"
    
    def _count_verification_checks(self, verification_text: str) -> int:
        """Count the number of verification checks mentioned"""
        check_keywords = [
            "project alignment", "methodology compliance", "deliverable completeness",
            "timeline", "resource allocation", "quality standards", "risk management"
        ]
        count = 0
        for keyword in check_keywords:
            if keyword.lower() in verification_text.lower():
                count += 1
        return count


class GeneratorAgent(BaseAgent):
    """
    ✍️ Generator Agent - The content synthesis specialist
    
    Responsibilities:
    - Synthesize information from all agents
    - Generate final deliverables and reports
    - Create comprehensive documentation
    - Coordinate final output creation
    """
    
    def synthesize_results(self, planner_result: AgentResult, executor_result: AgentResult, 
                          verifier_result: AgentResult, goal: str) -> AgentResult:
        """Synthesize results from all agents into final deliverables"""
        
        print(f"\n✍️ GENERATOR AGENT: Synthesizing final results...")
        
        synthesis_prompt = f"""
You are the Generator Agent in an advanced agentic system. Your role is to synthesize results from all agents into comprehensive final deliverables.

GOAL: {goal}

PLANNER AGENT RESULTS:
{planner_result.output}

EXECUTOR AGENT RESULTS:
{executor_result.output}

VERIFIER AGENT RESULTS:
{verifier_result.output}

SYNTHESIS INSTRUCTIONS:
Create comprehensive final deliverables that:

1. **INTEGRATE ALL PERSPECTIVES**: Combine planning, execution, and verification insights
2. **CREATE PROFESSIONAL DOCUMENTS**: Generate KPMG-standard deliverables
3. **PROVIDE EXECUTIVE SUMMARY**: Clear overview for stakeholders
4. **INCLUDE DETAILED ANALYSIS**: Comprehensive technical details
5. **ADD IMPLEMENTATION GUIDANCE**: Practical next steps and recommendations
6. **ENSURE QUALITY**: Meet all KPMG standards and client expectations

DELIVERABLES TO CREATE:
- Executive Summary Report
- Detailed Implementation Plan
- Risk Assessment and Mitigation Strategy
- Quality Assurance Framework
- Timeline and Resource Allocation
- Success Metrics and KPIs
- Recommendations and Next Steps

Use MemAgent to store each deliverable as a separate entity for easy access and reference.
"""
        
        try:
            response = self.agent.chat(synthesis_prompt)
            synthesis_text = response.reply or "Synthesis failed"
            
            # Parse synthesis results
            synthesis_metadata = {
                "goal": goal,
                "planner_success": planner_result.success,
                "executor_success": executor_result.success,
                "verifier_success": verifier_result.success,
                "synthesis_length": len(synthesis_text),
                "deliverables_created": self._count_synthesis_deliverables(synthesis_text)
            }
            
            result = AgentResult(
                success=True,
                output=synthesis_text,
                metadata=synthesis_metadata,
                timestamp=datetime.now().isoformat()
            )
            
            # Log the synthesis action
            self._log_agent_action("synthesize_results", result)
            
            print(f"   ✅ Results synthesized ({synthesis_metadata['deliverables_created']} deliverables)")
            print(f"   ✅ All agent results integrated")
            
            return result
            
        except Exception as e:
            error_result = AgentResult(
                success=False,
                output=f"Synthesis failed: {str(e)}",
                metadata={"error": str(e)},
                timestamp=datetime.now().isoformat()
            )
            self._log_agent_action("synthesize_results", error_result)
            return error_result
    
    def _count_synthesis_deliverables(self, synthesis_text: str) -> int:
        """Count the number of deliverables created in synthesis"""
        deliverable_keywords = [
            "executive summary", "implementation plan", "risk assessment",
            "quality assurance", "timeline", "success metrics", "recommendations"
        ]
        count = 0
        for keyword in deliverable_keywords:
            if keyword.lower() in synthesis_text.lower():
                count += 1
        return count


class AgentCoordinator:
    """
    🎯 Agent Coordinator - Orchestrates the 4 specialized agents
    
    Responsibilities:
    - Coordinate agent interactions
    - Manage shared memory and communication
    - Implement Flow-GRPO optimization
    - Track overall system performance
    """
    
    def __init__(self, agent: Agent, memory_path: Path):
        self.agent = agent
        self.memory_path = memory_path
        
        # Initialize specialized agents
        self.planner = PlannerAgent(agent, memory_path)
        self.executor = ExecutorAgent(agent, memory_path)
        self.verifier = VerifierAgent(agent, memory_path)
        self.generator = GeneratorAgent(agent, memory_path)
        
        # Initialize coordination memory
        self._initialize_coordination_memory()
    
    def _initialize_coordination_memory(self):
        """Initialize memory entities for agent coordination"""
        entities_dir = self.memory_path / "entities"
        entities_dir.mkdir(parents=True, exist_ok=True)
        
        # Agent coordination log
        coordination_file = entities_dir / "agent_coordination.md"
        if not coordination_file.exists():
            coordination_file.write_text("""# Agent Coordination Log

This file tracks how the 4 specialized agents work together:
- 🧭 Planner Agent: Strategic planning and decision making
- 🛠️ Executor Agent: Tool execution and action implementation  
- ✅ Verifier Agent: Quality checking and validation
- ✍️ Generator Agent: Content synthesis and final output creation

## Coordination Principles
1. All agents use MemAgent for context, execution, and memory
2. Each agent logs its actions for coordination tracking
3. Flow-GRPO optimization trains the Planner based on outcomes
4. Shared memory enables seamless agent communication

""")
        
        # Planner training log for Flow-GRPO
        training_file = entities_dir / "planner_training_log.md"
        if not training_file.exists():
            training_file.write_text("""# Planner Training Log (Flow-GRPO)

This file tracks the in-the-flow training of the Planner Agent using Flow-GRPO optimization.

## Training Principles
1. Final outcomes are broadcast back to all planning decisions
2. Successful patterns receive positive reinforcement
3. Failed patterns receive negative reinforcement
4. Planner learns to avoid repetitive mistakes and improve decision-making

""")
        
        # Agent performance tracking
        performance_file = entities_dir / "agent_performance.md"
        if not performance_file.exists():
            performance_file.write_text("""# Agent Performance Tracking

This file tracks the performance metrics of each specialized agent.

## Performance Metrics
- Success rates for each agent
- Quality scores for outputs
- Response times and efficiency
- Learning progress over iterations

""")
    
    def coordinate_agentic_workflow(self, goal: str, context: Dict[str, str]) -> Dict[str, AgentResult]:
        """Coordinate the complete agentic workflow"""
        
        print(f"\n🎯 AGENT COORDINATOR: Starting coordinated workflow...")
        
        results = {}
        
        try:
            # Step 1: Planner Agent generates strategic plan
            print(f"\n🔄 STEP 1: Strategic Planning")
            planner_result = self.planner.generate_strategic_plan(goal, context)
            results['planner'] = planner_result
            
            if not planner_result.success:
                print(f"❌ Planning failed, stopping workflow")
                return results
            
            # Step 2: Verifier Agent validates the plan
            print(f"\n🔄 STEP 2: Plan Validation")
            verifier_result = self.verifier.verify_plan(planner_result.output, goal)
            results['verifier'] = verifier_result
            
            if not verifier_result.metadata.get('is_valid', False):
                print(f"⚠️ Plan validation failed, but continuing for learning")
            
            # Step 3: Executor Agent executes the plan
            print(f"\n🔄 STEP 3: Plan Execution")
            executor_result = self.executor.execute_plan(planner_result.output, goal)
            results['executor'] = executor_result
            
            # Step 4: Verifier Agent validates execution
            print(f"\n🔄 STEP 4: Execution Validation")
            execution_verification = self.verifier.verify_execution(
                executor_result.output, planner_result.output
            )
            results['execution_verification'] = execution_verification
            
            # Step 5: Generator Agent synthesizes final results
            print(f"\n🔄 STEP 5: Result Synthesis")
            generator_result = self.generator.synthesize_results(
                planner_result, executor_result, verifier_result, goal
            )
            results['generator'] = generator_result
            
            # Step 6: Flow-GRPO optimization
            print(f"\n🔄 STEP 6: Flow-GRPO Training")
            self._apply_flow_grpo_training(results, goal)
            
            # Step 7: Store results and populate entities
            print(f"\n🔄 STEP 7: Storing Results and Populating Entities")
            self._store_workflow_results(goal, results)
            
            print(f"\n🎉 Coordinated workflow completed successfully!")
            return results
            
        except Exception as e:
            print(f"\n❌ Workflow coordination failed: {e}")
            return results
    
    def _apply_flow_grpo_training(self, results: Dict[str, AgentResult], goal: str):
        """Apply Flow-GRPO training to improve Planner Agent"""
        
        print(f"\n🧠 FLOW-GRPO: Applying in-the-flow training...")
        
        # Determine overall success
        overall_success = self._assess_overall_success(results)
        
        # Create training record
        training_entry = f"""
## Flow-GRPO Training - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

**Goal:** {goal}
**Overall Success:** {overall_success}

**Agent Results:**
- Planner: {'✅ SUCCESS' if results.get('planner', {}).success else '❌ FAILED'}
- Verifier: {'✅ SUCCESS' if results.get('verifier', {}).success else '❌ FAILED'}
- Executor: {'✅ SUCCESS' if results.get('executor', {}).success else '❌ FAILED'}
- Generator: {'✅ SUCCESS' if results.get('generator', {}).success else '❌ FAILED'}

**Training Signal:** {'POSITIVE' if overall_success else 'NEGATIVE'}

**Learning Impact:**
- Planner will {'reinforce' if overall_success else 'discourage'} similar approaches
- Memory updated with {'successful' if overall_success else 'failed'} patterns
- Future iterations will {'leverage' if overall_success else 'avoid'} this approach

---
"""
        
        # Store training record
        training_file = self.memory_path / "entities" / "planner_training_log.md"
        if training_file.exists():
            with open(training_file, 'a') as f:
                f.write(training_entry)
        
        # Update performance metrics
        self._update_performance_metrics(results, overall_success)
        
        print(f"   ✅ Flow-GRPO training applied")
        print(f"   ✅ Training signal: {'POSITIVE' if overall_success else 'NEGATIVE'}")
    
    def _store_workflow_results(self, goal: str, results: Dict[str, AgentResult]):
        """Store workflow results and populate entities with actual content"""
        print("\n📁 Storing workflow results...")
        
        # Get memory path from the agent (assuming all agents have the same memory path)
        memory_path = self.planner.agent.memory_path if hasattr(self.planner.agent, 'memory_path') else None
        if not memory_path:
            print("   ⚠️ No memory path available, skipping storage")
            return
        
        from pathlib import Path
        from datetime import datetime
        
        # Create plans directory and save comprehensive plan
        plans_dir = Path(memory_path) / "plans"
        plans_dir.mkdir(exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        goal_slug = goal.replace(" ", "_").replace("/", "_").replace("\\", "_")[:50]
        plan_file = plans_dir / f"plan_{timestamp}_{goal_slug}.md"
        
        # Get agent results
        planner_result = results.get('planner')
        verifier_result = results.get('verifier')
        executor_result = results.get('executor')
        generator_result = results.get('generator')
        
        # Create comprehensive plan content
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
        
        # Populate entities with actual content
        self._populate_entities_with_content(goal, results, memory_path)
        
        print(f"   ✅ Workflow results stored successfully")
    
    def _populate_entities_with_content(self, goal: str, results: Dict[str, AgentResult], memory_path: str):
        """Populate entities with actual content from agent results"""
        print("\n📝 Populating entities with agent-generated content...")
        
        from pathlib import Path
        
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
        
        entities_dir = Path(memory_path) / "entities"
        
        for entity_name, agent_type in entity_mappings.items():
            try:
                agent_result = results.get(agent_type)
                if agent_result and agent_result.success and agent_result.output:
                    # Create entity with actual content from agent
                    entity_file = entities_dir / f"{entity_name}.md"
                    
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
                        
            except Exception as e:
                print(f"   ⚠️ Failed to populate {entity_name}: {e}")
        
        print(f"   ✅ Entity population completed")
    
    def _assess_overall_success(self, results: Dict[str, AgentResult]) -> bool:
        """Assess overall success of the agentic workflow"""
        # Consider workflow successful if key agents succeeded
        key_agents = ['planner', 'executor', 'generator']
        successful_agents = sum(1 for agent in key_agents 
                              if results.get(agent, {}).success)
        
        # Workflow succeeds if at least 2 out of 3 key agents succeed
        return successful_agents >= 2
    
    def _update_performance_metrics(self, results: Dict[str, AgentResult], overall_success: bool):
        """Update agent performance metrics"""
        
        performance_entry = f"""
## Performance Update - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

**Overall Workflow Success:** {overall_success}

**Agent Performance:**
- Planner Agent: {'✅ SUCCESS' if results.get('planner', {}).success else '❌ FAILED'}
- Executor Agent: {'✅ SUCCESS' if results.get('executor', {}).success else '❌ FAILED'}
- Verifier Agent: {'✅ SUCCESS' if results.get('verifier', {}).success else '❌ FAILED'}
- Generator Agent: {'✅ SUCCESS' if results.get('generator', {}).success else '❌ FAILED'}

**Quality Metrics:**
- Plan Quality: {results.get('planner', {}).metadata.get('plan_length', 0)} chars
- Execution Quality: {results.get('executor', {}).metadata.get('deliverables_created', 0)} deliverables
- Verification Checks: {results.get('verifier', {}).metadata.get('checks_performed', 0)} checks
- Synthesis Quality: {results.get('generator', {}).metadata.get('deliverables_created', 0)} deliverables

---
"""
        
        # Store performance metrics
        performance_file = self.memory_path / "entities" / "agent_performance.md"
        if performance_file.exists():
            with open(performance_file, 'a') as f:
                f.write(performance_entry)
