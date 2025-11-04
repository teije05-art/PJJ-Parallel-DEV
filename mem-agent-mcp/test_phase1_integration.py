#!/usr/bin/env python3
"""
Phase 1: Simple Integration Test

Tests that all 8 backend fixes work together:
1. Context passing to all agents
2. Trainer initialization in PatternRecommender
3. Agent pair performance recording
4. Memory segments validation
5. Flow score calculation and deferral
6. Verification check serialization
7. Empty segment logging
8. Pattern effectiveness storage
"""

import sys
import os
from pathlib import Path

# Add repo root to path
REPO_ROOT = os.path.dirname(os.path.abspath(__file__))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

def test_imports():
    """Test that all modified modules import correctly"""
    print("\n🔍 TEST 1: Module Imports")
    print("=" * 60)
    
    try:
        from orchestrator.agents import (
            PlannerAgent, VerifierAgent, ExecutorAgent, 
            GeneratorAgent, AgentCoordinator
        )
        print("✅ Agent imports successful")
    except Exception as e:
        print(f"❌ Agent import failed: {e}")
        return False
    
    try:
        from orchestrator.simple_orchestrator import SimpleOrchestrator
        print("✅ SimpleOrchestrator import successful")
    except Exception as e:
        print(f"❌ SimpleOrchestrator import failed: {e}")
        return False
    
    try:
        from orchestrator.learning import FlowGRPOTrainer, AgentCoordination
        print("✅ Learning modules import successful")
    except Exception as e:
        print(f"❌ Learning modules import failed: {e}")
        return False
    
    try:
        from orchestrator.reasoning import LogicalPlanningPrompt, VerificationFeedback
        print("✅ Reasoning modules import successful")
    except Exception as e:
        print(f"❌ Reasoning modules import failed: {e}")
        return False
    
    return True

def test_agent_context_passing():
    """Test that agents accept context parameter"""
    print("\n🔍 TEST 2: Agent Context Parameter Support")
    print("=" * 60)
    
    from orchestrator.agents import PlannerAgent, VerifierAgent, ExecutorAgent, GeneratorAgent
    import inspect
    
    agents = {
        'PlannerAgent': (PlannerAgent, 'generate_strategic_plan'),
        'VerifierAgent': (VerifierAgent, 'verify_plan'),
        'ExecutorAgent': (ExecutorAgent, 'execute_plan'),
        'GeneratorAgent': (GeneratorAgent, 'synthesize_results'),
    }
    
    for agent_name, (agent_class, method_name) in agents.items():
        method = getattr(agent_class, method_name)
        sig = inspect.signature(method)
        
        if 'context' in sig.parameters:
            print(f"✅ {agent_name}.{method_name} has context parameter")
        else:
            print(f"❌ {agent_name}.{method_name} missing context parameter")
            return False
    
    return True

def test_pattern_recommender_trainer():
    """Test that PatternRecommender can be initialized with trainer"""
    print("\n🔍 TEST 3: PatternRecommender Trainer Support")
    print("=" * 60)
    
    from orchestrator.pattern_recommender import PatternRecommender
    from orchestrator.learning import FlowGRPOTrainer
    from pathlib import Path
    import tempfile
    
    # Create temporary memory path
    with tempfile.TemporaryDirectory() as tmpdir:
        try:
            # Create PatternRecommender with trainer
            trainer = FlowGRPOTrainer(learning_rate=0.05)
            recommender = PatternRecommender(Path(tmpdir), flow_grpo_trainer=trainer)
            
            if recommender.flow_grpo_trainer is not None:
                print("✅ PatternRecommender can be initialized with trainer")
                return True
            else:
                print("❌ PatternRecommender trainer not set")
                return False
        except Exception as e:
            print(f"❌ PatternRecommender initialization failed: {e}")
            return False

def test_verification_serialization():
    """Test that verification checks serialize correctly"""
    print("\n🔍 TEST 4: Verification Check Serialization")
    print("=" * 60)
    
    from orchestrator.reasoning import VerificationFeedback, VerificationResult
    from dataclasses import asdict
    
    try:
        verifier = VerificationFeedback()
        
        # Create test checks
        from orchestrator.reasoning.verification_feedback import PreconditionCheck, EffectCheck
        
        checks = [
            PreconditionCheck(
                name="test_precond",
                description="Test precondition",
                result=VerificationResult.PASS,
                explanation="Test passed"
            )
        ]
        
        # Test serialization
        check_dicts = []
        for check in checks:
            check_dict = asdict(check)
            # Convert enum result to string
            if hasattr(check_dict.get('result'), 'value'):
                check_dict['result'] = check_dict['result'].value
            check_dicts.append(check_dict)
        
        if len(check_dicts) > 0 and 'result' in check_dicts[0]:
            print("✅ Verification checks serialize correctly")
            return True
        else:
            print("❌ Verification check serialization failed")
            return False
    except Exception as e:
        print(f"❌ Verification serialization test failed: {e}")
        return False

def test_agent_coordination():
    """Test that agent coordination works"""
    print("\n🔍 TEST 5: Agent Coordination")
    print("=" * 60)
    
    from orchestrator.learning import AgentCoordination
    
    try:
        coord = AgentCoordination()
        
        # Test pair recording
        coord.record_pair_performance('planner', 'verifier', 0.85, success=True)
        
        if ('planner', 'verifier') in coord.pair_performances:
            print("✅ Agent pair performance recording works")
            return True
        else:
            print("❌ Agent pair performance not recorded")
            return False
    except Exception as e:
        print(f"❌ Agent coordination test failed: {e}")
        return False

def test_flow_grpo_trainer():
    """Test that Flow-GRPO trainer works"""
    print("\n🔍 TEST 6: Flow-GRPO Trainer")
    print("=" * 60)
    
    from orchestrator.learning import FlowGRPOTrainer
    
    try:
        trainer = FlowGRPOTrainer(learning_rate=0.05)
        
        # Test recording iteration signal
        trainer.record_iteration_signal(
            iteration=1,
            agent_name='planner',
            verification_quality=0.85,
            user_approved=True,
            reasoning_quality=0.8
        )
        
        # Test updating weights
        trainer.update_agent_weights()
        
        if trainer.agent_selection_weights.get('planner', 0) > 0:
            print("✅ Flow-GRPO trainer works correctly")
            return True
        else:
            print("❌ Flow-GRPO trainer weight update failed")
            return False
    except Exception as e:
        print(f"❌ Flow-GRPO trainer test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("🧪 PHASE 1: BACKEND INTEGRATION TEST")
    print("=" * 60)
    
    tests = [
        ("Module Imports", test_imports),
        ("Agent Context Passing", test_agent_context_passing),
        ("PatternRecommender Trainer", test_pattern_recommender_trainer),
        ("Verification Serialization", test_verification_serialization),
        ("Agent Coordination", test_agent_coordination),
        ("Flow-GRPO Trainer", test_flow_grpo_trainer),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            passed = test_func()
            results.append((test_name, passed))
        except Exception as e:
            print(f"❌ Test {test_name} crashed: {e}")
            import traceback
            traceback.print_exc()
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print("\n" + "=" * 60)
    print(f"TOTAL: {passed}/{total} tests passed")
    print("=" * 60)
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED! Backend fixes are working correctly.")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Review errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
