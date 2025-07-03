# Convergence Take-Home Test

> 🔍 **Welcome to the Pokédex!**  
> Type `exit` or `quit` to leave

---

## Quick Start

You can install all the dependencies with:

```bash
pip install -r requirements.txt
```

You can run the application directly with:

```bash
python src/main.py
```

## Getting Started with Docker

### Prerequisites

- Docker
- Docker Compose

### Development Setup

1. **Build and run the development environment:**

   ```bash
   make build
   ```

   then

   ```bash
   make start
   ```

2. **Add dependencies once in docker container:**
   Add new libraries in requirements/dev.in

   then

   ```bash
   make deps
   ```

## Project Structure

```
convergence-interview/
├── src/                    # Source code
│   └── main.py            # Main application entry point
├── tests/                 # Test files
├── requirements/          # Python dependencies
├── Dockerfile             # Docker image configuration
├── docker-compose.dev.yaml # Development Docker Compose
└── Makefile              # Common development commands
```

## Development

- All Python dependencies are managed through the `requirements/` directory
- The project uses Docker for consistent development environments
- If you want to add tests, put them in the `tests/` directory
- Implement your solution in the `src/` directory

Good luck with your take-home test!
