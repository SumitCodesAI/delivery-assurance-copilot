"""Jira API client wrapper."""

import logging
from typing import Dict, List, Optional

try:
    from jira import JIRA
    from jira.exceptions import JIRAError
    JIRA_AVAILABLE = True
except ImportError:
    JIRA_AVAILABLE = False
    JIRA = None

logger = logging.getLogger(__name__)


class JiraClient:
    """Wrapper around Jira Python client with error handling."""
    
    def __init__(self, url: str, username: str, api_token: str, timeout: int = 30):
        """
        Initialize Jira client.
        
        Args:
            url: Jira instance URL
            username: Jira username/email
            api_token: Jira API token
            timeout: Request timeout in seconds
        """
        if not JIRA_AVAILABLE:
            raise RuntimeError("jira-python package not installed. Run: pip install jira")
        
        self.url = url
        self.username = username
        self.timeout = timeout
        
        try:
            self.jira = JIRA(
                server=url,
                basic_auth=(username, api_token),
                timeout=timeout
            )
        except Exception as e:
            logger.error(f"Failed to initialize Jira client: {e}")
            raise
    
    def validate_connection(self) -> bool:
        """
        Test Jira connection.
        
        Returns:
            True if connection is valid, False otherwise
        """
        try:
            self.jira.myself()
            return True
        except Exception as e:
            logger.error(f"Jira connection validation failed: {e}")
            return False
    
    def get_project(self, project_key: str):
        """
        Get Jira project by key.
        
        Args:
            project_key: Project key (e.g., 'QUAL')
            
        Returns:
            Jira project object
        """
        return self.jira.project(project_key)
    
    def create_requirement_issue(
        self,
        project_key: str,
        requirement: Dict,
        parent_epic_key: Optional[str] = None
    ) -> str:
        """
        Create Jira issue from requirement.
        
        Args:
            project_key: Jira project key
            requirement: Requirement dict with fields
            parent_epic_key: Optional parent epic key
            
        Returns:
            Jira issue key (e.g., 'QUAL-101')
        """
        issue_dict = {
            'project': {'key': project_key},
            'issuetype': {'name': 'Story'},
            'summary': f"[REQ-{requirement.get('req_id', 'UNK')}] {requirement.get('title', 'Requirement')[:80]}",
            'description': self._format_requirement_description(requirement),
            'labels': ['auto-generated', 'requirements'],
            'priority': {'name': self._map_priority(requirement.get('priority', 'medium'))},
        }
        
        # Link to epic if provided
        if parent_epic_key:
            issue_dict['parent'] = {'key': parent_epic_key}
        
        try:
            issue = self.jira.create_issue(fields=issue_dict)
            logger.info(f"Created Jira issue {issue.key} for requirement {requirement.get('req_id')}")
            return issue.key
        except Exception as e:
            logger.error(f"Failed to create requirement issue: {e}")
            raise
    
    def create_test_issue(
        self,
        project_key: str,
        test_case: Dict,
        parent_issue_key: Optional[str] = None,
        requirement_key: Optional[str] = None
    ) -> str:
        """
        Create Jira issue from test case.
        
        Args:
            project_key: Jira project key
            test_case: Test case dict
            parent_issue_key: Optional parent issue key
            requirement_key: Optional requirement issue key to link to
            
        Returns:
            Jira issue key
        """
        issue_dict = {
            'project': {'key': project_key},
            'issuetype': {'name': 'Task'},  # Use Task since Test requires Zephyr
            'summary': f"[TEST] {test_case.get('title', 'Test Case')[:80]}",
            'description': self._format_test_description(test_case),
            'labels': ['auto-generated', 'test-cases'],
            'priority': {'name': self._map_priority(test_case.get('priority', 'medium'))},
        }
        
        if parent_issue_key:
            issue_dict['parent'] = {'key': parent_issue_key}
        
        try:
            issue = self.jira.create_issue(fields=issue_dict)
            logger.info(f"Created Jira issue {issue.key} for test case {test_case.get('id')}")
            
            # Link to requirement if provided
            if requirement_key:
                try:
                    self.jira.create_issue_link(
                        'relates to',
                        issue.key,
                        requirement_key
                    )
                    logger.info(f"Linked {issue.key} to {requirement_key}")
                except Exception as e:
                    logger.warning(f"Could not link {issue.key} to {requirement_key}: {e}")
            
            return issue.key
        except Exception as e:
            logger.error(f"Failed to create test issue: {e}")
            raise
    
    def create_epic(
        self,
        project_key: str,
        epic_title: str,
        epic_description: str = ""
    ) -> str:
        """
        Create Jira epic.
        
        Args:
            project_key: Jira project key
            epic_title: Epic title
            epic_description: Epic description
            
        Returns:
            Epic key
        """
        issue_dict = {
            'project': {'key': project_key},
            'issuetype': {'name': 'Epic'},
            'summary': epic_title,
            'description': epic_description or f"Auto-generated epic for test planning",
            'labels': ['auto-generated', 'test-planning'],
        }
        
        try:
            issue = self.jira.create_issue(fields=issue_dict)
            logger.info(f"Created epic {issue.key}")
            return issue.key
        except Exception as e:
            logger.error(f"Failed to create epic: {e}")
            raise
    
    def get_issues_by_jql(self, jql: str, max_results: int = 100) -> List:
        """
        Query Jira with JQL.
        
        Args:
            jql: JQL query
            max_results: Maximum results to return
            
        Returns:
            List of Jira issues
        """
        try:
            return self.jira.search_issues(jql, maxResults=max_results)
        except Exception as e:
            logger.error(f"JQL query failed: {e}")
            raise
    
    def get_issue_details(self, issue_key: str) -> Dict:
        """
        Get full issue details.
        
        Args:
            issue_key: Jira issue key
            
        Returns:
            Dict with issue details
        """
        try:
            issue = self.jira.issue(issue_key)
            return {
                'key': issue.key,
                'summary': issue.fields.summary,
                'description': issue.fields.description,
                'status': issue.fields.status.name,
                'priority': issue.fields.priority.name if issue.fields.priority else None,
                'assignee': issue.fields.assignee.name if issue.fields.assignee else None,
                'created': str(issue.fields.created),
                'updated': str(issue.fields.updated),
            }
        except Exception as e:
            logger.error(f"Failed to get issue details for {issue_key}: {e}")
            raise
    
    def update_issue_status(self, issue_key: str, target_status: str):
        """
        Update issue status.
        
        Args:
            issue_key: Jira issue key
            target_status: Target status name (e.g., 'Done', 'In Progress')
        """
        try:
            issue = self.jira.issue(issue_key)
            transitions = self.jira.transitions(issue)
            
            # Find matching transition
            transition = next(
                (t for t in transitions['transitions'] if t['name'].lower() == target_status.lower()),
                None
            )
            
            if transition:
                self.jira.transition_issue(issue, transition['id'])
                logger.info(f"Updated {issue_key} status to {target_status}")
            else:
                logger.warning(f"Transition to {target_status} not available for {issue_key}")
        except Exception as e:
            logger.error(f"Failed to update issue status: {e}")
            raise
    
    @staticmethod
    def _format_requirement_description(requirement: Dict) -> str:
        """Format requirement as Jira description."""
        return f"""
{requirement.get('description', 'No description provided')}

---
*Auto-Generated by Delivery Assurance Copilot*
- Requirement ID: {requirement.get('req_id', 'N/A')}
- Priority: {requirement.get('priority', 'Medium')}
- Ambiguity Flag: {requirement.get('ambiguity_flag', False)}
- Ambiguity Notes: {requirement.get('ambiguity_notes', 'N/A')}
"""
    
    @staticmethod
    def _format_test_description(test_case: Dict) -> str:
        """Format test case as Jira description."""
        steps_text = ""
        steps = test_case.get('steps', [])
        if isinstance(steps, list):
            steps_text = '\n'.join([
                f"{i+1}. {step.get('action', '')} → {step.get('expected_outcome', '')}"
                if isinstance(step, dict)
                else f"{i+1}. {step}"
                for i, step in enumerate(steps)
            ])
        
        return f"""
**Preconditions**: {test_case.get('preconditions', 'None')}

**Steps**:
{steps_text}

**Expected Result**: {test_case.get('expected_result', 'N/A')}

---
*Auto-Generated by Delivery Assurance Copilot*
- Test ID: {test_case.get('id', 'N/A')}
- Priority: {test_case.get('priority', 'Medium')}
"""
    
    @staticmethod
    def _map_priority(priority_str: str) -> str:
        """Map priority string to Jira priority."""
        priority_map = {
            'high': 'High',
            'medium': 'Medium',
            'low': 'Low',
        }
        return priority_map.get(priority_str.lower(), 'Medium')
