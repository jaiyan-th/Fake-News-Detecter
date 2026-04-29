# Contributing to Fake News Detection System

Thank you for your interest in contributing to our AI-powered fake news detection system! We welcome contributions from the community.

## 🚀 Getting Started

### Prerequisites
- Python 3.8 or higher
- Git
- Basic knowledge of Flask, NLP, or machine learning

### Development Setup

1. **Fork the repository**
   ```bash
   git clone https://github.com/yourusername/fake-news-detector.git
   cd fake-news-detector
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   cd fake-news-detector
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Add your API keys to .env
   ```

5. **Run tests**
   ```bash
   python -m pytest tests/
   ```

## 🛠️ How to Contribute

### Reporting Issues
- Use the GitHub issue tracker
- Provide detailed description and steps to reproduce
- Include system information and error messages

### Submitting Changes

1. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes**
   - Follow the coding standards below
   - Add tests for new functionality
   - Update documentation as needed

3. **Test your changes**
   ```bash
   python -m pytest tests/
   python test_rag_pipeline.py  # For RAG pipeline changes
   ```

4. **Commit your changes**
   ```bash
   git add .
   git commit -m "feat: add your feature description"
   ```

5. **Push and create a pull request**
   ```bash
   git push origin feature/your-feature-name
   ```

## 📝 Coding Standards

### Python Code Style
- Follow PEP 8 guidelines
- Use meaningful variable and function names
- Add docstrings for all functions and classes
- Maximum line length: 88 characters (Black formatter)

### JavaScript Code Style
- Use ES6+ features
- Follow consistent naming conventions
- Add comments for complex logic
- Use semicolons consistently

### Documentation
- Update README.md for new features
- Add inline comments for complex algorithms
- Include examples in docstrings
- Update API documentation for new endpoints

## 🧪 Testing Guidelines

### Unit Tests
- Write tests for all new functions
- Aim for >80% code coverage
- Use descriptive test names
- Mock external API calls

### Integration Tests
- Test complete workflows
- Verify API endpoints work correctly
- Test error handling scenarios

### Example Test Structure
```python
def test_analyze_text_real_news():
    """Test that real news is correctly identified."""
    result = pipeline.analyze_text("Legitimate news content...")
    assert result['verdict'] == 'REAL'
    assert float(result['confidence'].rstrip('%')) > 70
```

## 🎯 Areas for Contribution

### High Priority
- [ ] Multi-language support improvements
- [ ] Performance optimizations
- [ ] Additional trusted news sources
- [ ] Enhanced error handling

### Medium Priority
- [ ] Image analysis with OCR
- [ ] Social media integration
- [ ] Real-time monitoring dashboard
- [ ] Custom model training

### Documentation
- [ ] API documentation improvements
- [ ] Tutorial videos
- [ ] Deployment guides
- [ ] Architecture diagrams

## 🔍 Code Review Process

1. All submissions require review
2. Maintainers will review within 48 hours
3. Address feedback promptly
4. Ensure CI/CD checks pass
5. Squash commits before merging

## 📋 Pull Request Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Documentation update
- [ ] Performance improvement

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests pass
- [ ] Manual testing completed

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] No breaking changes
```

## 🏷️ Commit Message Format

Use conventional commits:
- `feat:` new features
- `fix:` bug fixes
- `docs:` documentation changes
- `style:` formatting changes
- `refactor:` code refactoring
- `test:` adding tests
- `chore:` maintenance tasks

Example: `feat: add multi-language support for Hindi`

## 🤝 Community Guidelines

- Be respectful and inclusive
- Provide constructive feedback
- Help newcomers get started
- Follow the code of conduct
- Ask questions if unsure

## 📞 Getting Help

- GitHub Discussions for questions
- GitHub Issues for bugs
- Email: jaiyanth.b@outlook.com
- Check existing documentation first

## 🙏 Recognition

Contributors will be:
- Listed in the README
- Mentioned in release notes
- Invited to maintainer discussions (for significant contributions)

Thank you for contributing to making news verification more accessible and reliable!