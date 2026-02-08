# Security Policy

## Supported Versions

This project is currently in active development. Security updates are provided for the latest version.

| Version | Supported          |
| ------- | ------------------ |
| Latest  | ✅                 |
| < Latest | ❌                 |

## Reporting a Vulnerability

To report a security vulnerability:

1. **Use GitHub's Security Advisory feature**: Go to the repository's "Security" tab and click "Report a vulnerability"
2. **Do not open public issues** for security vulnerabilities
3. **Include in your report**:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Any suggested fixes

The maintainers will respond to security reports within 48 hours and work to release a fix as soon as possible.

## Security Considerations

### For Mobile App Deployment

- Use HTTPS in production (required for voice recognition and PWA features)
- Implement authentication for the API endpoints
- Add rate limiting to prevent abuse
- Use environment variables for sensitive configuration
- Never commit Roku IP addresses or credentials to version control

### For Alexa Lambda Deployment

- Store Roku IP securely (use environment variables or AWS Systems Manager Parameter Store)
- Implement proper error handling to avoid leaking sensitive information
- Keep dependencies up to date
- Use AWS IAM roles with minimal required permissions

### General Best Practices

- Keep all dependencies updated regularly
- Review code changes for security issues before deployment
- Enable "Control by mobile apps" on Roku only when needed
- Use VPN for remote access rather than exposing the API to the internet

## Automated Security Scanning

This repository uses several automated security scanning tools:

- **Bandit**: Scans Python code for common security issues (runs in CI)
- **CodeQL**: Semantic code analysis via GitHub Code Scanning (default setup)
  - Configured through GitHub repository settings (Security > Code security and analysis)
  - Runs automatically on push and pull requests
  - Weekly scheduled scans to detect new vulnerabilities

**Note**: This project uses GitHub's CodeQL default setup rather than a custom workflow to avoid configuration conflicts. The default setup provides comprehensive security scanning with automatic updates to detection rules.
