"""
Example usage of the Learning Orchestrator

This shows how the loop works with concrete examples.
"""

from orchestrator import LearningOrchestrator
from pathlib import Path


def run_simple_example():
    """
    Run a simple example with a basic goal.
    
    This will:
    1. Initialize the orchestrator
    2. Run the learning loop
    3. Show how memory accumulates over iterations
    """
    print("="*80)
    print("🎯 SIMPLE EXAMPLE: Infrastructure Setup")
    print("="*80)
    print()
    print("This example shows how the orchestrator:")
    print("  1. Starts with minimal context")
    print("  2. Generates plans with chain-of-thought reasoning")
    print("  3. Validates with MemAgent")
    print("  4. Gets your approval")
    print("  5. Learns from each iteration")
    print()
    input("Press Enter to start...")
    
    # Get memory path
    repo_root = Path(__file__).parent.parent
    memory_path_file = repo_root / ".memory_path"
    
    if memory_path_file.exists():
        memory_path = memory_path_file.read_text().strip()
    else:
        memory_path = "/Users/teije/Desktop/memagent/local-memory"
    
    # Initialize orchestrator
    orchestrator = LearningOrchestrator(
        memory_path=memory_path,
        max_iterations=5  # Shorter for example
    )
    
    # Run with a simple goal
    goal = "Set up basic orchestrator infrastructure"
    
    orchestrator.run_learning_loop(goal)
    
    print("\n✅ Example complete!")
    print("\nCheck these files to see what was learned:")
    print(f"  - {memory_path}/entities/execution_log.md")
    print(f"  - {memory_path}/entities/successful_patterns.md")
    print(f"  - {memory_path}/entities/planning_errors.md")


def run_multi_iteration_example():
    """
    Run multiple iterations to show learning progression.
    """
    print("="*80)
    print("🎯 MULTI-ITERATION EXAMPLE: Progressive Learning")
    print("="*80)
    print()
    print("This example will run multiple iterations to demonstrate:")
    print("  - How context accumulates in memory")
    print("  - How plans improve with learned patterns")
    print("  - How the system avoids past mistakes")
    print()
    input("Press Enter to start...")
    
    repo_root = Path(__file__).parent.parent
    memory_path_file = repo_root / ".memory_path"
    memory_path = memory_path_file.read_text().strip() if memory_path_file.exists() else "/Users/teije/Desktop/memagent/local-memory"
    
    orchestrator = LearningOrchestrator(
        memory_path=memory_path,
        max_iterations=10
    )
    
    goal = "Develop and test the complete multi-agent orchestrator system"
    
    orchestrator.run_learning_loop(goal)


def show_learning_progression():
    """
    Show how learning progresses across iterations.
    """
    print("="*80)
    print("📊 LEARNING PROGRESSION VISUALIZATION")
    print("="*80)
    print()
    
    repo_root = Path(__file__).parent.parent
    memory_path_file = repo_root / ".memory_path"
    memory_path = memory_path_file.read_text().strip() if memory_path_file.exists() else "/Users/teije/Desktop/memagent/local-memory"
    
    memory_path = Path(memory_path)
    
    # Read execution log
    execution_log = memory_path / "entities" / "execution_log.md"
    if execution_log.exists():
        content = execution_log.read_text()
        successes = content.count("SUCCESS ✅")
        print(f"✅ Successful iterations: {successes}")
    else:
        print("No execution log yet - run the orchestrator first!")
        return
    
    # Read successful patterns
    patterns = memory_path / "entities" / "successful_patterns.md"
    if patterns.exists():
        content = patterns.read_text()
        pattern_count = content.count("### Pattern")
        print(f"📚 Learned patterns: {pattern_count}")
        print()
        print("Successful patterns learned:")
        print("-" * 80)
        print(content)
    
    # Read errors
    errors = memory_path / "entities" / "planning_errors.md"
    if errors.exists():
        content = errors.read_text()
        error_count = content.count("### Error")
        print(f"\n❌ Error patterns to avoid: {error_count}")
        if error_count > 0:
            print()
            print("Mistakes learned from:")
            print("-" * 80)
            print(content)


if __name__ == "__main__":
    import sys
    
    print("🚀 Learning Orchestrator Examples")
    print()
    print("Choose an example:")
    print("  1. Simple example (5 iterations)")
    print("  2. Multi-iteration example (10 iterations)")
    print("  3. Show learning progression")
    print()
    
    choice = input("Enter choice (1-3): ").strip()
    
    if choice == "1":
        run_simple_example()
    elif choice == "2":
        run_multi_iteration_example()
    elif choice == "3":
        show_learning_progression()
    else:
        print("Invalid choice!")
        sys.exit(1)

