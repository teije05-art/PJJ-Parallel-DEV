# MemAgent-Modular: AI Learning Orchestrator

A sophisticated AI learning orchestrator system that integrates with Claude Desktop through MCP (Model Context Protocol) to provide persistent learning capabilities across multiple domains. The system learns from each interaction and progressively improves its planning and execution capabilities.

## 🚀 Features

### Core Capabilities
- **Persistent Learning**: Accumulates knowledge in memory files that persist across sessions
- **Progressive Improvement**: Each iteration builds on previous successes and learns from failures
- **Domain-Agnostic Planning**: Works across healthcare, technology, manufacturing, retail, financial, QSR, and general domains
- **Multi-Agent Coordination**: 4-agent system with specialized roles and Flow-GRPO training
- **Natural Language Interface**: Seamless integration with Claude Desktop
- **Memory Management**: Unlimited capacity memory system with no hallucinations

### Learning System
- **6-Step Learning Loop**: Retrieve → Generate → Validate → Approve → Execute → Learn
- **Memory Accumulation**: Context grows from ~500 chars to 6000+ chars over 15 iterations
- **Success Rate Improvement**: Improves from ~60% to 90%+ over iterations
- **Error Learning**: Documents and learns from planning mistakes
- **Pattern Recognition**: Identifies and reuses successful approaches

### Supported Domains
- **Healthcare**: Clinical development, regulatory approval, medical device market analysis
- **Technology**: Startup development, product-market fit, digital transformation
- **Manufacturing**: Supply chain optimization, lean manufacturing, industrial market entry
- **Retail**: Consumer behavior analysis, e-commerce development, retail expansion
- **Financial Services**: Banking frameworks, fintech development, financial market analysis
- **QSR (Quick Service Restaurant)**: Restaurant operations, food service market study, franchise development
- **General Strategic Planning**: Long-term planning with iterative improvement

## 🏗️ Architecture

```
Claude Desktop (Frontend)
    ↓ (MCP Protocol)
MCP Server (mcp_server/server.py)
    ├── use_memory_agent
    ├── start_planning_iteration
    ├── approve_current_plan
    ├── reject_current_plan
    ├── view_learning_summary
    └── list_entities
    ↓
Enhanced Orchestrator + Llama + MemAgent
    ├── orchestrator/ directory
    │   ├── goal_analyzer.py (domain detection)
    │   ├── domain_templates.py (7 domain templates)
    │   ├── agentflow_agents.py (4-agent coordination)
    │   ├── simple_orchestrator.py (main orchestrator)
    │   └── context_manager.py
    ├── Llama 3.3 70B (Fireworks/vLLM)
    └── MemAgent memory system
```

## 📁 Project Structure

```
memagent-modular/
├── mem-agent-mcp/                 # Main system directory
│   ├── agent/                     # Core agent implementation
│   ├── mcp_server/               # MCP server implementation
│   ├── memory_connectors/        # Memory system connectors
│   ├── orchestrator/             # Learning orchestrator
│   │   ├── goal_analyzer.py      # Dynamic domain detection
│   │   ├── domain_templates.py   # Domain-specific templates
│   │   ├── agentflow_agents.py   # 4-agent coordination system
│   │   ├── simple_orchestrator.py # Main orchestrator
│   │   └── context_manager.py    # Context management
│   ├── memory-bankk/             # Memory bank documentation
│   └── pyproject.toml            # Project dependencies
├── local-memory/                 # Memory system storage
│   ├── entities/                 # Memory entities
│   ├── plans/                    # Generated plans
│   └── deliverables/             # Generated deliverables
└── documentation files           # Project documentation
```

## 🛠️ Installation & Setup

### Prerequisites
- Python 3.8+
- Claude Desktop with MCP configuration
- Either Fireworks API key (Mac) or vLLM setup (Linux)

### Quick Start

1. **Clone the repository**
   ```bash
   git clone https://github.com/teije05-art/pjj-websearcherror.git
   cd pjj-websearcherror
   ```

2. **Install dependencies**
   ```bash
   cd mem-agent-mcp
   make install
   ```

3. **Setup memory directory**
   ```bash
   make setup
   ```

4. **Generate MCP configuration**
   ```bash
   make generate-mcp-json
   ```

5. **Start MCP server**
   ```bash
   make serve-mcp
   ```

6. **Configure Claude Desktop**
   - Copy the generated `mcp.json` content to your Claude Desktop configuration
   - Restart Claude Desktop to pick up new tools

### Memory Configuration

Create a `.memory_path` file to specify your memory directory:
```bash
echo "/path/to/your/memory" > .memory_path
```

## 🎯 Usage

### Starting a Planning Iteration

In Claude Desktop, simply say:
```
"Start a planning iteration for [your goal]"
```

For example:
- "Start a planning iteration for developing a healthcare market entry strategy"
- "Start a planning iteration for creating a fintech startup business plan"
- "Start a planning iteration for optimizing a manufacturing supply chain"

### Available MCP Tools

- **`start_planning_iteration`**: Begin new planning iteration with goal
- **`approve_current_plan`**: Approve current plan for execution
- **`reject_current_plan`**: Reject current plan with feedback
- **`view_learning_summary`**: View accumulated learning progress
- **`list_entities`**: Browse all available entities in memory system
- **`use_memory_agent`**: Query memory system with natural language

### Learning Modes

1. **Manual Mode**: Human approval required for each iteration
2. **Semi-Autonomous Mode**: Auto-approve valid plans with periodic checkpoints

## 🧠 Memory System

The system maintains several key memory entities:

- **`execution_log.md`**: Tracks successful iterations with timestamps
- **`successful_patterns.md`**: Records proven approaches and methodologies
- **`planning_errors.md`**: Documents rejected plans and mistakes to avoid
- **`agent_performance.md`**: Tracks performance metrics for each agent
- **`planner_training_log.md`**: Records Flow-GRPO training signals

## 🔧 Configuration

### Backend Configuration

The system automatically detects your platform:
- **Mac**: Uses Fireworks API (requires API key)
- **Linux**: Uses vLLM (requires local setup)

### MCP Configuration

Example `mcp.json`:
```json
{
  "mcpServers": {
    "memory-agent-stdio": {
      "command": "bash",
      "args": ["-lc", "cd /path/to/mem-agent-mcp && uv run python mcp_server/server.py"],
      "env": {
        "FASTMCP_LOG_LEVEL": "INFO",
        "MCP_TRANSPORT": "stdio",
        "FIREWORKS_API_KEY": "your_key_here"
      }
    }
  }
}
```

## 📊 Performance Metrics

### Target Performance
- **Iteration Time**: ~30 seconds per iteration
- **Success Rate**: 60% → 90%+ over 15 iterations
- **Context Growth**: 500 chars → 6000+ chars over 15 iterations
- **Memory Usage**: ~500 MB RAM, 1-2 GB VRAM (temporary)

### Learning Curve
- **Iterations 1-5**: Basic patterns learned, ~60% success rate
- **Iterations 6-10**: Patterns refined, ~75% success rate
- **Iterations 11-15**: Sophisticated understanding, ~90% success rate
- **Iterations 15+**: Expert level, ~95%+ success rate

## 🧪 Testing

### Running Tests
```bash
# Test MCP server
cd mem-agent-mcp
make test

# Test orchestrator
cd orchestrator
python -m pytest tests/
```

### Manual Testing
1. Start MCP server: `make serve-mcp`
2. Restart Claude Desktop
3. Try different domain goals
4. Monitor memory file updates
5. Verify learning progression

## 📚 Documentation

- **`ARCHITECTURE.md`**: Detailed system architecture
- **`PLANNING_SYSTEM_FLOWCHART.md`**: Visual system flow
- **`memory-bankk/`**: Comprehensive memory bank documentation
- **`orchestrator/`**: Orchestrator-specific documentation

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

For questions, issues, or contributions:
- Open an issue on GitHub
- Check the documentation in `memory-bankk/`
- Review the architecture documentation

## 🔮 Roadmap

- [ ] Enhanced domain templates
- [ ] Advanced learning algorithms
- [ ] Multi-project support
- [ ] Web interface
- [ ] API endpoints
- [ ] Cloud deployment options

---

**Note**: This system is designed for learning and experimentation. Always review generated plans before implementation in production environments.
