"""GitHub Connector implementation."""

import httpx
from typing import Any, Optional

from connectors.sdk import BaseConnector, retry
from shared.logging import get_logger

logger = get_logger(__name__)


class GitHubConnector(BaseConnector):
    """GitHub connector for repository and PR management."""
    
    def __init__(self, config: dict):
        """Initialize GitHub connector.
        
        Args:
            config: Configuration with token and optionally base_url
        """
        super().__init__(config)
        self.client: Optional[httpx.AsyncClient] = None
        self.base_url = self.get_config("base_url", "https://api.github.com")
    
    async def connect(self) -> bool:
        """Establish GitHub connection."""
        try:
            if not self.validate_config(["token"]):
                return False
            
            self.client = httpx.AsyncClient(
                headers={
                    "Authorization": f"token {self.get_config('token')}",
                    "Accept": "application/vnd.github.v3+json"
                },
                timeout=30.0
            )
            
            # Test connection
            response = await self.client.get(f"{self.base_url}/user")
            
            if response.status_code == 200:
                data = response.json()
                self.connected = True
                logger.info("github_connected", user=data.get("login"))
                return True
            else:
                logger.error("github_connection_failed", status=response.status_code)
                return False
                
        except Exception as e:
            logger.error("github_connection_failed", error=str(e))
            self.connected = False
            return False
    
    async def disconnect(self) -> bool:
        """Close GitHub connection."""
        if self.client:
            await self.client.aclose()
            self.client = None
        self.connected = False
        logger.info("github_disconnected")
        return True
    
    async def health_check(self) -> dict:
        """Check GitHub connection health."""
        try:
            if not self.client:
                return {"status": "disconnected", "healthy": False}
            
            response = await self.client.get(f"{self.base_url}/user")
            
            if response.status_code == 200:
                data = response.json()
                self.health_status = "healthy"
                return {
                    "status": "healthy",
                    "healthy": True,
                    "user": data.get("login")
                }
            else:
                self.health_status = "unhealthy"
                return {
                    "status": "unhealthy",
                    "healthy": False,
                    "error": f"HTTP {response.status_code}"
                }
                
        except Exception as e:
            self.health_status = "unhealthy"
            return {
                "status": "unhealthy",
                "healthy": False,
                "error": str(e)
            }
    
    @retry(max_attempts=3)
    async def execute(self, method: str, **kwargs) -> Any:
        """Execute GitHub connector method.
        
        Args:
            method: Method name
            **kwargs: Method parameters
            
        Returns:
            Method execution result
        """
        if not self.connected:
            await self.connect()
        
        method_map = {
            "list_repositories": self.list_repositories,
            "get_repository": self.get_repository,
            "create_pull_request": self.create_pull_request,
            "list_pull_requests": self.list_pull_requests,
            "merge_pull_request": self.merge_pull_request,
            "create_issue": self.create_issue,
            "list_deployments": self.list_deployments,
            "create_deployment": self.create_deployment,
        }
        
        if method not in method_map:
            raise ValueError(f"Unknown method: {method}")
        
        return await method_map[method](**kwargs)
    
    async def list_repositories(self, org: Optional[str] = None) -> list:
        """List repositories.
        
        Args:
            org: Organization name (optional, lists user repos if not provided)
            
        Returns:
            List of repositories
        """
        if org:
            url = f"{self.base_url}/orgs/{org}/repos"
        else:
            url = f"{self.base_url}/user/repos"
        
        response = await self.client.get(url)
        
        if response.status_code == 200:
            repos = response.json()
            return [
                {
                    "name": repo["name"],
                    "full_name": repo["full_name"],
                    "private": repo["private"],
                    "default_branch": repo["default_branch"],
                    "url": repo["html_url"]
                }
                for repo in repos
            ]
        else:
            return []
    
    async def get_repository(self, owner: str, repo: str) -> dict:
        """Get repository details.
        
        Args:
            owner: Repository owner
            repo: Repository name
            
        Returns:
            Repository details
        """
        response = await self.client.get(f"{self.base_url}/repos/{owner}/{repo}")
        
        if response.status_code == 200:
            data = response.json()
            return {
                "name": data["name"],
                "full_name": data["full_name"],
                "description": data.get("description"),
                "private": data["private"],
                "default_branch": data["default_branch"],
                "language": data.get("language"),
                "stars": data["stargazers_count"],
                "forks": data["forks_count"],
                "url": data["html_url"]
            }
        else:
            return None
    
    async def create_pull_request(
        self,
        owner: str,
        repo: str,
        title: str,
        head: str,
        base: str,
        body: Optional[str] = None
    ) -> dict:
        """Create pull request.
        
        Args:
            owner: Repository owner
            repo: Repository name
            title: PR title
            head: Head branch
            base: Base branch
            body: PR description (optional)
            
        Returns:
            PR details
        """
        payload = {
            "title": title,
            "head": head,
            "base": base
        }
        
        if body:
            payload["body"] = body
        
        response = await self.client.post(
            f"{self.base_url}/repos/{owner}/{repo}/pulls",
            json=payload
        )
        
        if response.status_code == 201:
            data = response.json()
            logger.info("github_pr_created", pr_number=data["number"])
            return {
                "success": True,
                "pr_number": data["number"],
                "url": data["html_url"],
                "state": data["state"]
            }
        else:
            return {"success": False, "error": f"HTTP {response.status_code}"}
    
    async def list_pull_requests(
        self,
        owner: str,
        repo: str,
        state: str = "open"
    ) -> list:
        """List pull requests.
        
        Args:
            owner: Repository owner
            repo: Repository name
            state: PR state (open, closed, all)
            
        Returns:
            List of PRs
        """
        response = await self.client.get(
            f"{self.base_url}/repos/{owner}/{repo}/pulls",
            params={"state": state}
        )
        
        if response.status_code == 200:
            prs = response.json()
            return [
                {
                    "number": pr["number"],
                    "title": pr["title"],
                    "state": pr["state"],
                    "user": pr["user"]["login"],
                    "created_at": pr["created_at"],
                    "url": pr["html_url"]
                }
                for pr in prs
            ]
        else:
            return []
    
    async def merge_pull_request(
        self,
        owner: str,
        repo: str,
        pr_number: int,
        commit_message: Optional[str] = None
    ) -> dict:
        """Merge pull request.
        
        Args:
            owner: Repository owner
            repo: Repository name
            pr_number: PR number
            commit_message: Merge commit message (optional)
            
        Returns:
            Merge result
        """
        payload = {}
        if commit_message:
            payload["commit_message"] = commit_message
        
        response = await self.client.put(
            f"{self.base_url}/repos/{owner}/{repo}/pulls/{pr_number}/merge",
            json=payload
        )
        
        if response.status_code == 200:
            data = response.json()
            logger.info("github_pr_merged", pr_number=pr_number)
            return {
                "success": True,
                "merged": data["merged"],
                "sha": data["sha"]
            }
        else:
            return {"success": False, "error": f"HTTP {response.status_code}"}
    
    async def create_issue(
        self,
        owner: str,
        repo: str,
        title: str,
        body: Optional[str] = None,
        labels: Optional[list] = None
    ) -> dict:
        """Create issue.
        
        Args:
            owner: Repository owner
            repo: Repository name
            title: Issue title
            body: Issue description (optional)
            labels: Issue labels (optional)
            
        Returns:
            Issue details
        """
        payload = {"title": title}
        
        if body:
            payload["body"] = body
        if labels:
            payload["labels"] = labels
        
        response = await self.client.post(
            f"{self.base_url}/repos/{owner}/{repo}/issues",
            json=payload
        )
        
        if response.status_code == 201:
            data = response.json()
            return {
                "success": True,
                "issue_number": data["number"],
                "url": data["html_url"]
            }
        else:
            return {"success": False, "error": f"HTTP {response.status_code}"}
    
    async def list_deployments(self, owner: str, repo: str) -> list:
        """List deployments.
        
        Args:
            owner: Repository owner
            repo: Repository name
            
        Returns:
            List of deployments
        """
        response = await self.client.get(
            f"{self.base_url}/repos/{owner}/{repo}/deployments"
        )
        
        if response.status_code == 200:
            deployments = response.json()
            return [
                {
                    "id": dep["id"],
                    "ref": dep["ref"],
                    "environment": dep["environment"],
                    "created_at": dep["created_at"]
                }
                for dep in deployments
            ]
        else:
            return []
    
    async def create_deployment(
        self,
        owner: str,
        repo: str,
        ref: str,
        environment: str = "production"
    ) -> dict:
        """Create deployment.
        
        Args:
            owner: Repository owner
            repo: Repository name
            ref: Git ref to deploy
            environment: Deployment environment
            
        Returns:
            Deployment details
        """
        payload = {
            "ref": ref,
            "environment": environment,
            "auto_merge": False
        }
        
        response = await self.client.post(
            f"{self.base_url}/repos/{owner}/{repo}/deployments",
            json=payload
        )
        
        if response.status_code == 201:
            data = response.json()
            return {
                "success": True,
                "deployment_id": data["id"],
                "environment": data["environment"]
            }
        else:
            return {"success": False, "error": f"HTTP {response.status_code}"}
