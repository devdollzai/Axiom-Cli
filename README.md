# Sovereign Axiom
@DevDollzAi / @AxiomHive

A high-performance hybrid Python/Rust framework for AI agent orchestration, LLM inference, and distributed computing.

## Features

- **Multi-Language Architecture**: Combines Python's flexibility with Rust's performance
- **Agent Management**: Advanced planning, debugging, and execution agents
- **LLM Integration**: Optimized inference with caching and batching
- **Memory Systems**: Efficient vector storage and retrieval
- **Git Integration**: Automated version control operations

## Project Structure

```
sovereign-axion/
├── python/                    # Python modules
│   ├── agents/               # AI agents (planner, debug, LLM, git)
│   ├── embedding_model.py    # Vector embeddings
│   ├── llm_inference.py      # Language model inference
│   ├── memory.py             # Memory management
│   └── sovereign_cli.py      # Command-line interface
├── axion-core/               # Rust core library
│   └── src/
│       ├── lib.rs
│       └── orchestrator.rs
├── requirements.txt          # Python dependencies
├── Cargo.toml               # Rust workspace configuration
└── README.md
```

## Prerequisites

- Python 3.8+
- Rust 1.70+
- CMake (for Rust dependencies)

## Installation

### Python Setup

Create a virtual environment (recommended):

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### Rust Setup

```bash
cargo build --release
```

## Usage

### Basic Example

```python
from sovereign_axion.python.agents.planner_agent import PlannerAgent
from sovereign_axion.python.llm_inference import LLMInference

# Initialize components
planner = PlannerAgent()
llm = LLMInference()

# Execute a task
result = planner.plan_and_execute("Analyze this dataset")
```

### CLI Usage

```bash
python python/sovereign_cli.py --help
```

## Development

### Running Tests

```bash
# Python tests
python -m pytest python/test_*.py

# Rust tests
cargo test
```

### Building Documentation

```bash
# Generate docs
cargo doc --open
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Security

This project does not require elevated privileges or system modifications. All operations are contained within user space and do not tamper with system configurations.
