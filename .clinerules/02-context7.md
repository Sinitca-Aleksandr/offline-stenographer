# Context7 Integration Rules

## Overview
Context7 is the primary MCP server for code generation, library documentation, setup instructions, and configuration guidance. It provides up-to-date, accurate information from official documentation sources.

## When to Use Context7

### Required Usage
- **Code Generation**: When generating code examples, boilerplate, or implementation patterns
- **Library Documentation**: When needing API references, method signatures, or usage examples
- **Setup & Configuration**: When configuring tools, frameworks, or development environments
- **Best Practices**: When seeking current standards and recommended approaches

### Automatic Usage
Use Context7 tools automatically without explicit user request for:
- Framework-specific implementation patterns
- Library API documentation and examples
- Configuration file templates and setup instructions
- Dependency management and integration guides

## Usage Workflow

### 1. Library Resolution
Always use `resolve-library-id` first to get the correct Context7-compatible library ID:
- Format: `/org/project` or `/org/project/version`
- Example: `/vercel/next.js` or `/mongodb/docs/v8.0`

### 2. Documentation Retrieval
Use `get-library-docs` with the resolved library ID to get:
- API documentation
- Code examples
- Configuration guides
- Setup instructions

## Integration with Memory Bank

Context7 documentation should be integrated into the Memory Bank when it provides:
- New technical patterns or architectural decisions
- Important configuration or setup information
- Library-specific best practices
- Integration requirements or constraints

## Examples

### Use Context7 For:
- "How do I implement authentication in Next.js?"
- "Show me the MongoDB aggregation pipeline syntax"
- "What's the recommended way to configure ESLint for React?"
- "How do I set up Docker for a Python Flask application?"

### Don't Use Context7 For:
- Project-specific business logic
- Custom implementation details
- User-specific requirements
- Memory Bank updates (use standard documentation process)

## Best Practices

1. **Proactive Usage**: Anticipate documentation needs and use Context7 before asking users
2. **Contextual Integration**: Weave retrieved information naturally into responses
3. **Version Awareness**: Specify versions when relevant (e.g., React 18 vs 19)
4. **Error Handling**: If library resolution fails, ask user for clarification rather than guessing
5. **Memory Bank Updates**: Document significant findings in appropriate Memory Bank files
