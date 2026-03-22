# Contributing to Cloud Native AI Lab

Thank you for your interest in contributing! This project is a community learning resource for Kubernetes engineers new to AI workloads.

## How to contribute

### Reporting issues

- Found an outdated version number or broken lab step? Open an issue.
- Include the lab number, step number, and what you expected vs. what happened.
- If a version number has changed since publication, include a link to the official source.

### Fixing bugs

1. Fork the repository.
2. Create a branch from `staging` (not `main`).
3. Make your fix.
4. Run the test suite: `./scripts/test.sh`
5. Submit a pull request targeting `staging`.

### Adding or updating content

- **Project one-pagers** (`docs/projects/`): Follow the template in the existing files. Every fact must be verifiable against official documentation.
- **Lab exercises** (`labs/`): Follow the lab README template. Every step must actually work — do not submit untested instructions.
- **Manifests**: All YAML must be valid. Test on a kind cluster before submitting.

### What we value

- **Accuracy over speed.** Every version number, CNCF status, and technical claim must be verifiable. Link to official sources.
- **Honesty over completeness.** If a lab step does not work on kind without GPU hardware, say so. Provide annotated manifests with conceptual walkthroughs rather than broken instructions.
- **Clarity over cleverness.** Write for Kubernetes practitioners who have never touched AI/ML workloads. Use analogies to familiar K8s concepts.
- **No marketing language.** This is a community resource. No "revolutionary," "game-changing," or vendor promotion.

### Style guide

- Use clear, factual language appropriate for technical documentation.
- Labs should follow the progression: explain the concept, do the exercise, verify it worked, explain what happened.
- Shell scripts must include progress indicators for any operation that takes more than a few seconds.
- All code files start with a 2-line ABOUTME comment.

## Branch workflow

- All work targets the `staging` branch.
- After review and testing, maintainers merge `staging` to `main`.
- Never submit pull requests directly to `main`.

## Code of conduct

Be respectful, constructive, and welcoming. This is a learning resource — questions are encouraged.

## License

By contributing, you agree that your contributions will be licensed under the Apache License 2.0.
