"""Content filter service module."""
from typing import Dict, List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
import re


class ContentFilterService:
    """Content filter service class."""

    def __init__(self, session: AsyncSession, config: Dict):
        """Initialize content filter service."""
        self._config = config
        self._blocked_domains = set(config.get("BLOCKED_DOMAINS", []))
        self._blocked_keywords = set(config.get("BLOCKED_KEYWORDS", []))
        self._content_rules = config.get("CONTENT_RULES", {})
        self._sensitivity_level = config.get("SENSITIVITY_LEVEL", "medium")

    def filter_web_content(
        self,
        content: str,
        content_type: str,
        sensitivity: Optional[str] = None
    ) -> Dict:
        """Filter web content based on rules and sensitivity."""
        if sensitivity is None:
            sensitivity = self._sensitivity_level

        filtered_content = content
        issues = []

        # Apply keyword filtering
        keyword_issues = self._filter_keywords(filtered_content)
        issues.extend(keyword_issues)

        # Apply content type specific rules
        type_issues = self._apply_content_type_rules(
            filtered_content, content_type)
        issues.extend(type_issues)

        # Apply sensitivity level rules
        sensitivity_issues = self._apply_sensitivity_rules(
            filtered_content, sensitivity)
        issues.extend(sensitivity_issues)

        return {
            "filtered_content": filtered_content,
            "has_issues": bool(issues),
            "issues": issues,
            "sensitivity_level": sensitivity
        }

    def filter_url(self, url: str) -> Dict:
        """Filter URL based on blocked domains and patterns."""
        issues = []

        # Check for blocked domains
        domain = self._extract_domain(url)
        if domain in self._blocked_domains:
            issues.append({
                "type": "blocked_domain",
                "message": f"Domain {domain} is blocked"
            })

        # Check URL patterns
        pattern_issues = self._check_url_patterns(url)
        issues.extend(pattern_issues)

        return {
            "url": url,
            "is_blocked": bool(issues),
            "issues": issues
        }

    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL."""
        # Simple domain extraction, could be enhanced with urllib.parse
        match = re.search(
            r"^(?:https?:\/\/)?(?:[^@\n]+@)?(?:www\.)?([^:\/\n?]+)", url)
        return match.group(1) if match else ""

    def _filter_keywords(self, content: str) -> List[Dict]:
        """Filter content based on blocked keywords."""
        issues = []
        for keyword in self._blocked_keywords:
            if keyword.lower() in content.lower():
                issues.append({
                    "type": "blocked_keyword",
                    "message": f"Content contains blocked keyword: {keyword}"
                })
        return issues

    def _apply_content_type_rules(
        self,
        content: str,
        content_type: str
    ) -> List[Dict]:
        """Apply content type specific filtering rules."""
        issues = []
        if content_type in self._content_rules:
            rules = self._content_rules[content_type]
            for rule in rules:
                if "pattern" in rule:
                    if re.search(rule["pattern"], content, re.IGNORECASE):
                        issues.append({
                            "type": "content_rule",
                            "message": rule.get("message", "Content violates rules")
                        })
        return issues

    def _apply_sensitivity_rules(
        self,
        content: str,
        sensitivity: str
    ) -> List[Dict]:
        """Apply sensitivity level specific rules."""
        issues = []
        sensitivity_rules = {
            "high": {
                "max_length": 1000,
                "patterns": [
                    r"(?i)(password|credit.?card|ssn|social.?security)",
                    r"(?i)(private|confidential|secret)"
                ]
            },
            "medium": {
                "max_length": 5000,
                "patterns": [
                    r"(?i)(password|credit.?card)",
                ]
            },
            "low": {
                "max_length": 10000,
                "patterns": []
            }
        }

        rules = sensitivity_rules.get(sensitivity, sensitivity_rules["medium"])

        # Check content length
        if len(content) > rules["max_length"]:
            issues.append({
                "type": "content_length",
                "message": f"Content exceeds maximum length for {sensitivity} sensitivity"
            })

        # Check patterns
        for pattern in rules["patterns"]:
            if re.search(pattern, content):
                issues.append({
                    "type": "sensitive_content",
                    "message": "Content contains sensitive information"
                })

        return issues

    def _check_url_patterns(self, url: str) -> List[Dict]:
        """Check URL against suspicious patterns."""
        issues = []
        suspicious_patterns = [
            (r"(?i)(adult|xxx|porn)", "Adult content"),
            (r"(?i)(hack|crack|warez)", "Potentially harmful content"),
            (r"(?i)(phish|malware|spam)", "Suspicious content")
        ]

        for pattern, message in suspicious_patterns:
            if re.search(pattern, url):
                issues.append({
                    "type": "suspicious_url",
                    "message": message
                })

        return issues

    def update_blocked_domains(self, domains: List[str]) -> None:
        """Update blocked domains list."""
        self._blocked_domains.update(domains)

    def update_blocked_keywords(self, keywords: List[str]) -> None:
        """Update blocked keywords list."""
        self._blocked_keywords.update(keywords)

    def set_sensitivity_level(self, level: str) -> None:
        """Set content filter sensitivity level."""
        valid_levels = ["low", "medium", "high"]
        if level not in valid_levels:
            raise ValueError(
                f"Invalid sensitivity level. Must be one of: {valid_levels}")
        self._sensitivity_level = level
