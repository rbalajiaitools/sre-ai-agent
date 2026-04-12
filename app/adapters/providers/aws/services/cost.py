"""Cost Explorer service for cost data."""

import boto3
from botocore.exceptions import ClientError

from app.adapters.models import CostRequest, CostResponse
from app.adapters.providers.aws.mappers import map_cost_entry
from app.core.logging import get_logger

logger = get_logger(__name__)


class CostExplorerService:
    """Service for querying AWS Cost Explorer."""

    def __init__(self, session: boto3.Session) -> None:
        """Initialize Cost Explorer service.

        Args:
            session: Authenticated boto3 session
        """
        self.session = session
        self.ce_client = session.client("ce")

    def get_cost(self, request: CostRequest) -> CostResponse:
        """Get cost data from Cost Explorer.

        Args:
            request: Cost request

        Returns:
            CostResponse with cost breakdown
        """
        logger.info(
            "fetching_cost_data",
            start_time=request.start_time,
            end_time=request.end_time,
        )

        try:
            # Build group by
            group_by = []
            for dimension in request.group_by:
                group_by.append({
                    "Type": "DIMENSION",
                    "Key": dimension.upper(),
                })

            # Get cost and usage
            response = self.ce_client.get_cost_and_usage(
                TimePeriod={
                    "Start": request.start_time.strftime("%Y-%m-%d"),
                    "End": request.end_time.strftime("%Y-%m-%d"),
                },
                Granularity=request.granularity.upper(),
                Metrics=["UnblendedCost"],
                GroupBy=group_by if group_by else [],
            )

            # Calculate total cost
            total_cost = 0.0
            currency = "USD"
            breakdown = []

            for result in response.get("ResultsByTime", []):
                # Get total for this time period
                if "Total" in result:
                    amount = float(result["Total"]["UnblendedCost"]["Amount"])
                    total_cost += amount
                    currency = result["Total"]["UnblendedCost"]["Unit"]

                # Get breakdown by groups
                for group in result.get("Groups", []):
                    keys = group.get("Keys", [])
                    metrics = group.get("Metrics", {})

                    if keys and metrics:
                        dimension = request.group_by[0] if request.group_by else "SERVICE"
                        dimension_value = keys[0]

                        cost_entry = map_cost_entry(
                            cost_data=metrics,
                            dimension=dimension,
                            dimension_value=dimension_value,
                        )
                        breakdown.append(cost_entry)

            logger.info(
                "cost_data_fetched",
                total_cost=total_cost,
                currency=currency,
            )

            return CostResponse(
                total_cost=total_cost,
                currency=currency,
                breakdown=breakdown,
                source_provider="aws",
            )

        except ClientError as e:
            logger.error(
                "cost_explorer_error",
                error=str(e),
                error_code=e.response.get("Error", {}).get("Code"),
            )
            raise
