# Security Policy

## Supported Versions

We provide security updates for the following versions of CrisisMap AI:

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |
| < 1.0   | :x:                |

## Reporting a Vulnerability

We take the security of CrisisMap AI seriously. If you believe you have found a security vulnerability, please report it to us as described below.

### How to Report

**Please do not report security vulnerabilities through public GitHub issues.**

Instead, please send an email to security@crisismap.ai (or to the maintainers directly) with the following information:

1. **Subject Line**: "Security Vulnerability Report - CrisisMap AI"
2. **Description**: A clear description of the vulnerability
3. **Steps to Reproduce**: Detailed steps to reproduce the issue
4. **Impact**: Your assessment of the potential impact
5. **Suggested Fix**: If you have suggestions for how to fix the issue

### What to Include

Please include as much of the following information as possible:

- Type of issue (e.g., buffer overflow, SQL injection, cross-site scripting, etc.)
- Full paths of source file(s) related to the manifestation of the issue
- The location of the affected source code (tag/branch/commit or direct URL)
- Any special configuration required to reproduce the issue
- Step-by-step instructions to reproduce the issue
- Proof-of-concept or exploit code (if possible)
- Impact of the issue, including how an attacker might exploit the issue

### Response Timeline

- **Initial Response**: Within 48 hours of receiving your report
- **Investigation**: We will investigate and provide updates within 7 days
- **Fix Development**: Critical issues will be addressed within 30 days
- **Disclosure**: We will coordinate disclosure timeline with you

## Security Measures

### Current Security Implementations

1. **Input Validation**
   - All user inputs are validated and sanitized
   - Query parameters are properly escaped
   - File uploads are restricted and validated

2. **Authentication & Authorization**
   - API key authentication for external access
   - Rate limiting on all endpoints
   - CORS configuration for web interface

3. **Data Protection**
   - Environment variables for sensitive configuration
   - Secure database connections (MongoDB Atlas)
   - No sensitive data in logs

4. **Infrastructure Security**
   - Docker containerization with non-root user
   - Health checks and monitoring
   - Secure default configurations

### Planned Security Enhancements

1. **Enhanced Authentication**
   - JWT token-based authentication
   - Role-based access control (RBAC)
   - OAuth integration

2. **Advanced Security Headers**
   - Content Security Policy (CSP)
   - HTTP Strict Transport Security (HSTS)
   - X-Frame-Options and X-Content-Type-Options

3. **Monitoring & Alerting**
   - Security event logging
   - Intrusion detection
   - Automated vulnerability scanning

## Security Best Practices for Contributors

### Code Security

1. **Input Validation**
   ```python
   # Good: Validate and sanitize inputs
   def search_events(query: str, limit: int = 10):
       if not query or len(query.strip()) < 3:
           raise ValueError("Query must be at least 3 characters")
       if limit > 100:
           raise ValueError("Limit cannot exceed 100")
       # ... rest of function
   ```

2. **SQL Injection Prevention**
   ```python
   # Good: Use parameterized queries
   collection.find({"title": {"$regex": query, "$options": "i"}})
   
   # Bad: String concatenation
   # collection.find({"title": {"$regex": f".*{query}.*"}})
   ```

3. **Error Handling**
   ```python
   # Good: Don't expose internal details
   try:
       result = database_operation()
   except DatabaseError:
       logger.error("Database operation failed", exc_info=True)
       raise HTTPException(status_code=500, detail="Internal server error")
   ```

### Environment Security

1. **Secrets Management**
   - Never commit secrets to version control
   - Use environment variables or secret management services
   - Rotate secrets regularly

2. **Dependencies**
   - Keep dependencies updated
   - Use `safety` to check for known vulnerabilities
   - Pin dependency versions in production

3. **Configuration**
   - Use secure defaults
   - Disable debug mode in production
   - Configure proper logging levels

### Deployment Security

1. **Container Security**
   - Run containers as non-root user
   - Use minimal base images
   - Scan images for vulnerabilities

2. **Network Security**
   - Use HTTPS in production
   - Configure firewalls properly
   - Implement rate limiting

3. **Monitoring**
   - Enable access logging
   - Monitor for suspicious activity
   - Set up alerting for security events

## Vulnerability Disclosure Process

### For Security Researchers

1. **Scope**: This policy applies to the CrisisMap AI application and its infrastructure
2. **Rules of Engagement**:
   - Do not access, modify, or delete data belonging to others
   - Do not perform attacks that could harm the availability of our services
   - Do not perform attacks against our users or attempt to social engineer our staff
   - Do not make reports that you have not personally verified

3. **Out of Scope**:
   - Denial of service attacks
   - Social engineering attacks against our team or users
   - Attacks requiring physical access to our infrastructure
   - Issues in third-party services that we do not control

### Coordinated Disclosure

We believe in coordinated disclosure and will work with security researchers to:

1. Confirm the vulnerability and determine its impact
2. Develop and test a fix
3. Release the fix to users
4. Coordinate public disclosure

We request that you:
- Give us reasonable time to address the issue before public disclosure
- Make a good faith effort to avoid destructive attacks
- Do not access or modify user data

## Security Tools and Processes

### Automated Security Checks

We use the following tools to maintain security:

1. **Code Analysis**
   - `bandit` for Python security linting
   - `safety` for dependency vulnerability scanning
   - `semgrep` for additional security pattern detection

2. **Infrastructure Scanning**
   - Container image vulnerability scanning
   - Dependency checking in CI/CD pipeline
   - Regular security audits

### Security Testing

1. **Static Analysis**: Automated security code review
2. **Dependency Scanning**: Regular checks for vulnerable dependencies
3. **Container Scanning**: Security scanning of Docker images
4. **Penetration Testing**: Periodic security assessments

## Incident Response

### Security Incident Process

1. **Detection**: Security issue identified through monitoring, reports, or testing
2. **Assessment**: Evaluate severity and potential impact
3. **Containment**: Implement immediate measures to limit damage
4. **Investigation**: Determine root cause and scope of impact
5. **Remediation**: Deploy fixes and verify effectiveness
6. **Recovery**: Restore normal operations
7. **Lessons Learned**: Document incident and improve processes

### Communication

- **Internal**: Immediate notification to development team
- **Users**: Transparent communication about issues affecting them
- **Public**: Responsible disclosure after fixes are deployed

## Security Contacts

- **Security Email**: security@crisismap.ai
- **GPG Key**: [Public key for encrypted communications]
- **Response Time**: Within 48 hours for initial response

## Acknowledgments

We appreciate the security research community's efforts to improve the security of open source software. Security researchers who responsibly disclose vulnerabilities will be acknowledged in our security advisories (with their permission).

## Legal

This security policy is provided in good faith to encourage responsible vulnerability disclosure. It does not create any legal obligations or rights. We reserve the right to modify this policy at any time.

---

**Last Updated**: January 2025
**Version**: 1.0