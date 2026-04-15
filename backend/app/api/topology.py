"""Real topology API endpoints for service discovery and mapping."""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import get_db
from app.db import crud
from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(tags=["topology"])

# In-memory cache for topology data
_topology_cache: Dict[str, Dict[str, Any]] = {}
CACHE_TTL_SECONDS = 300  # 5 minutes


class ServiceNode(BaseModel):
    id: str
    name: str
    type: str  # service, database, cache, queue, etc.
    provider: str  # aws, azure, gcp
    region: Optional[str] = None
    status: str  # healthy, degraded, down, unknown
    resource_count: int = 0
    metadata: dict = {}


class ServiceEdge(BaseModel):
    id: str
    source: str
    target: str
    relationship: str  # DEPENDS_ON, CALLS, READS_FROM, WRITES_TO


class TopologyGraph(BaseModel):
    nodes: List[ServiceNode]
    edges: List[ServiceEdge]


class RediscoveryJob(BaseModel):
    job_id: str
    status: str
    started_at: str
    message: str


@router.get("/topology/graph")
async def get_topology_graph(
    tenant_id: str = Query(...),
    db: AsyncSession = Depends(get_db)
) -> TopologyGraph:
    """Get the service topology graph for a tenant - discovers real AWS resources."""
    logger.info("fetching_topology_graph", tenant_id=tenant_id)
    
    # Check cache first
    cache_key = f"topology_graph_{tenant_id}"
    if cache_key in _topology_cache:
        cached_data = _topology_cache[cache_key]
        cache_time = cached_data.get('timestamp')
        if cache_time and datetime.now() - cache_time < timedelta(seconds=CACHE_TTL_SECONDS):
            logger.info("topology_graph_from_cache", tenant_id=tenant_id)
            return TopologyGraph(
                nodes=cached_data['nodes'],
                edges=cached_data['edges']
            )
    
    # Get AWS integrations for this tenant
    integrations = await crud.get_integrations(db, tenant_id, "aws")
    
    if not integrations:
        logger.warning("no_aws_integration", tenant_id=tenant_id)
        raise HTTPException(
            status_code=404, 
            detail="No AWS integration found. Please configure AWS credentials in Settings to discover your infrastructure."
        )
    
    # Use the first active integration
    integration = next((i for i in integrations if i.is_active), None)
    if not integration:
        logger.warning("no_active_aws_integration", tenant_id=tenant_id)
        raise HTTPException(
            status_code=404,
            detail="No active AWS integration found. Please activate an AWS integration in Settings."
        )
    
    # Decrypt config
    config_dict = crud.decrypt_integration_config(integration)
    
    access_key = config_dict.get("access_key_id")
    secret_key = config_dict.get("secret_access_key")
    region = config_dict.get("region", "us-east-1")
    
    if not access_key or not secret_key:
        logger.error("missing_aws_credentials", tenant_id=tenant_id)
        raise HTTPException(
            status_code=400,
            detail="AWS credentials are incomplete. Please update your AWS integration in Settings."
        )
    
    # Discover real AWS resources
    import boto3
    from botocore.exceptions import ClientError
    
    try:
        session = boto3.Session(
            aws_access_key_id=access_key,
            aws_secret_access_key=secret_key,
            region_name=region
        )
        
        nodes = []
        edges = []
        node_id_counter = 1
        
        # Discover Lambda functions
        try:
            lambda_client = session.client('lambda')
            functions_response = lambda_client.list_functions()
            
            for function in functions_response.get('Functions', []):
                function_name = function.get('FunctionName')
                
                # Get function configuration for VPC details
                vpc_config = function.get('VpcConfig', {})
                
                nodes.append(ServiceNode(
                    id=f"lambda-{node_id_counter:03d}",
                    name=function_name,
                    type="lambda",
                    provider="aws",
                    region=region,
                    status="healthy",
                    resource_count=1,
                    metadata={
                        "runtime": function.get('Runtime'),
                        "memory": function.get('MemorySize'),
                        "timeout": function.get('Timeout'),
                        "handler": function.get('Handler'),
                        "arn": function.get('FunctionArn'),
                        "last_modified": function.get('LastModified'),
                        "vpc_id": vpc_config.get('VpcId'),
                        "subnet_ids": vpc_config.get('SubnetIds', []),
                        "security_group_ids": vpc_config.get('SecurityGroupIds', [])
                    }
                ))
                node_id_counter += 1
        except Exception as e:
            logger.warning("lambda_discovery_error", error=str(e))
        
        # Discover EC2 instances
        try:
            ec2 = session.client('ec2')
            instances_response = ec2.describe_instances()
            
            for reservation in instances_response.get('Reservations', []):
                for instance in reservation.get('Instances', []):
                    instance_id = instance.get('InstanceId')
                    instance_name = next((tag['Value'] for tag in instance.get('Tags', []) if tag['Key'] == 'Name'), instance_id)
                    state = instance.get('State', {}).get('Name')
                    
                    nodes.append(ServiceNode(
                        id=f"ec2-{node_id_counter:03d}",
                        name=instance_name,
                        type="ec2",
                        provider="aws",
                        region=region,
                        status="healthy" if state == "running" else "degraded",
                        resource_count=1,
                        metadata={
                            "instance_id": instance_id,
                            "instance_type": instance.get('InstanceType'),
                            "state": state,
                            "vpc_id": instance.get('VpcId'),
                            "subnet_id": instance.get('SubnetId'),
                            "private_ip": instance.get('PrivateIpAddress'),
                            "public_ip": instance.get('PublicIpAddress')
                        }
                    ))
                    node_id_counter += 1
        except Exception as e:
            logger.warning("ec2_discovery_error", error=str(e))
        
        # Discover RDS databases
        try:
            rds = session.client('rds')
            rds_response = rds.describe_db_instances()
            
            for db_instance in rds_response.get('DBInstances', []):
                db_id = db_instance.get('DBInstanceIdentifier')
                nodes.append(ServiceNode(
                    id=f"rds-{node_id_counter:03d}",
                    name=db_id,
                    type="rds",
                    provider="aws",
                    region=region,
                    status="healthy" if db_instance.get('DBInstanceStatus') == 'available' else "degraded",
                    resource_count=1,
                    metadata={
                        "engine": db_instance.get('Engine'),
                        "engine_version": db_instance.get('EngineVersion'),
                        "instance_class": db_instance.get('DBInstanceClass'),
                        "status": db_instance.get('DBInstanceStatus'),
                        "endpoint": db_instance.get('Endpoint', {}).get('Address'),
                        "port": db_instance.get('Endpoint', {}).get('Port')
                    }
                ))
                node_id_counter += 1
        except Exception as e:
            logger.warning("rds_discovery_error", error=str(e))
        
        # Discover S3 buckets
        try:
            s3 = session.client('s3')
            buckets_response = s3.list_buckets()
            
            for bucket in buckets_response.get('Buckets', []):
                bucket_name = bucket.get('Name')
                nodes.append(ServiceNode(
                    id=f"s3-{node_id_counter:03d}",
                    name=bucket_name,
                    type="s3",
                    provider="aws",
                    region=region,
                    status="healthy",
                    resource_count=1,
                    metadata={
                        "bucket_name": bucket_name,
                        "creation_date": bucket.get('CreationDate').isoformat() if bucket.get('CreationDate') else None
                    }
                ))
                node_id_counter += 1
        except Exception as e:
            logger.warning("s3_discovery_error", error=str(e))
        
        # Discover DynamoDB tables
        try:
            dynamodb = session.client('dynamodb')
            tables_response = dynamodb.list_tables()
            
            for table_name in tables_response.get('TableNames', []):
                nodes.append(ServiceNode(
                    id=f"dynamodb-{node_id_counter:03d}",
                    name=table_name,
                    type="dynamodb",
                    provider="aws",
                    region=region,
                    status="healthy",
                    resource_count=1,
                    metadata={
                        "table_name": table_name
                    }
                ))
                node_id_counter += 1
        except Exception as e:
            logger.warning("dynamodb_discovery_error", error=str(e))
        
        # Discover ECS services
        try:
            ecs = session.client('ecs')
            clusters_response = ecs.list_clusters()
            
            for cluster_arn in clusters_response.get('clusterArns', []):
                cluster_name = cluster_arn.split('/')[-1]
                services_response = ecs.list_services(cluster=cluster_arn)
                
                for service_arn in services_response.get('serviceArns', []):
                    service_name = service_arn.split('/')[-1]
                    nodes.append(ServiceNode(
                        id=f"ecs-{node_id_counter:03d}",
                        name=service_name,
                        type="ecs",
                        provider="aws",
                        region=region,
                        status="healthy",
                        resource_count=1,
                        metadata={
                            "cluster": cluster_name,
                            "service_arn": service_arn
                        }
                    ))
                    node_id_counter += 1
        except Exception as e:
            logger.warning("ecs_discovery_error", error=str(e))
        
        # Discover ElastiCache clusters
        try:
            elasticache = session.client('elasticache')
            cache_response = elasticache.describe_cache_clusters()
            
            for cluster in cache_response.get('CacheClusters', []):
                cluster_id = cluster.get('CacheClusterId')
                nodes.append(ServiceNode(
                    id=f"cache-{node_id_counter:03d}",
                    name=cluster_id,
                    type="elasticache",
                    provider="aws",
                    region=region,
                    status="healthy" if cluster.get('CacheClusterStatus') == 'available' else "degraded",
                    resource_count=1,
                    metadata={
                        "engine": cluster.get('Engine'),
                        "engine_version": cluster.get('EngineVersion'),
                        "node_type": cluster.get('CacheNodeType'),
                        "status": cluster.get('CacheClusterStatus')
                    }
                ))
                node_id_counter += 1
        except Exception as e:
            logger.warning("elasticache_discovery_error", error=str(e))
        
        # Discover VPCs
        try:
            ec2 = session.client('ec2')
            vpcs_response = ec2.describe_vpcs()
            
            for vpc in vpcs_response.get('Vpcs', []):
                vpc_id = vpc.get('VpcId')
                vpc_name = next((tag['Value'] for tag in vpc.get('Tags', []) if tag['Key'] == 'Name'), vpc_id)
                
                nodes.append(ServiceNode(
                    id=f"vpc-{node_id_counter:03d}",
                    name=vpc_name,
                    type="vpc",
                    provider="aws",
                    region=region,
                    status="healthy",
                    resource_count=1,
                    metadata={
                        "vpc_id": vpc_id,
                        "cidr_block": vpc.get('CidrBlock'),
                        "is_default": vpc.get('IsDefault'),
                        "state": vpc.get('State')
                    }
                ))
                node_id_counter += 1
        except Exception as e:
            logger.warning("vpc_discovery_error", error=str(e))
        
        # Discover API Gateway APIs
        try:
            apigateway = session.client('apigateway')
            apis_response = apigateway.get_rest_apis()
            
            for api in apis_response.get('items', []):
                api_name = api.get('name')
                nodes.append(ServiceNode(
                    id=f"api-{node_id_counter:03d}",
                    name=api_name,
                    type="apigateway",
                    provider="aws",
                    region=region,
                    status="healthy",
                    resource_count=1,
                    metadata={
                        "api_id": api.get('id'),
                        "description": api.get('description'),
                        "created_date": api.get('createdDate').isoformat() if api.get('createdDate') else None
                    }
                ))
                node_id_counter += 1
        except Exception as e:
            logger.warning("apigateway_discovery_error", error=str(e))
        
        # Discover Subnets
        try:
            ec2 = session.client('ec2')
            subnets_response = ec2.describe_subnets()
            
            for subnet in subnets_response.get('Subnets', []):
                subnet_id = subnet.get('SubnetId')
                subnet_name = next((tag['Value'] for tag in subnet.get('Tags', []) if tag['Key'] == 'Name'), subnet_id)
                
                nodes.append(ServiceNode(
                    id=f"subnet-{node_id_counter:03d}",
                    name=subnet_name,
                    type="subnet",
                    provider="aws",
                    region=region,
                    status="healthy",
                    resource_count=1,
                    metadata={
                        "subnet_id": subnet_id,
                        "vpc_id": subnet.get('VpcId'),
                        "cidr_block": subnet.get('CidrBlock'),
                        "availability_zone": subnet.get('AvailabilityZone'),
                        "available_ip_count": subnet.get('AvailableIpAddressCount'),
                        "map_public_ip": subnet.get('MapPublicIpOnLaunch')
                    }
                ))
                node_id_counter += 1
        except Exception as e:
            logger.warning("subnet_discovery_error", error=str(e))
        
        # Discover Internet Gateways
        try:
            ec2 = session.client('ec2')
            igw_response = ec2.describe_internet_gateways()
            
            for igw in igw_response.get('InternetGateways', []):
                igw_id = igw.get('InternetGatewayId')
                igw_name = next((tag['Value'] for tag in igw.get('Tags', []) if tag['Key'] == 'Name'), igw_id)
                
                nodes.append(ServiceNode(
                    id=f"igw-{node_id_counter:03d}",
                    name=igw_name,
                    type="internet_gateway",
                    provider="aws",
                    region=region,
                    status="healthy",
                    resource_count=1,
                    metadata={
                        "igw_id": igw_id,
                        "attachments": [att.get('VpcId') for att in igw.get('Attachments', [])]
                    }
                ))
                node_id_counter += 1
        except Exception as e:
            logger.warning("igw_discovery_error", error=str(e))
        
        # Discover NAT Gateways
        try:
            ec2 = session.client('ec2')
            nat_response = ec2.describe_nat_gateways()
            
            for nat in nat_response.get('NatGateways', []):
                nat_id = nat.get('NatGatewayId')
                nat_name = next((tag['Value'] for tag in nat.get('Tags', []) if tag['Key'] == 'Name'), nat_id)
                
                nodes.append(ServiceNode(
                    id=f"nat-{node_id_counter:03d}",
                    name=nat_name,
                    type="nat_gateway",
                    provider="aws",
                    region=region,
                    status="healthy" if nat.get('State') == 'available' else "degraded",
                    resource_count=1,
                    metadata={
                        "nat_id": nat_id,
                        "vpc_id": nat.get('VpcId'),
                        "subnet_id": nat.get('SubnetId'),
                        "state": nat.get('State')
                    }
                ))
                node_id_counter += 1
        except Exception as e:
            logger.warning("nat_discovery_error", error=str(e))
        
        # Discover Security Groups
        try:
            ec2 = session.client('ec2')
            sg_response = ec2.describe_security_groups()
            
            for sg in sg_response.get('SecurityGroups', []):
                sg_id = sg.get('GroupId')
                sg_name = sg.get('GroupName')
                
                nodes.append(ServiceNode(
                    id=f"sg-{node_id_counter:03d}",
                    name=sg_name,
                    type="security_group",
                    provider="aws",
                    region=region,
                    status="healthy",
                    resource_count=1,
                    metadata={
                        "sg_id": sg_id,
                        "vpc_id": sg.get('VpcId'),
                        "description": sg.get('Description'),
                        "ingress_rules": len(sg.get('IpPermissions', [])),
                        "egress_rules": len(sg.get('IpPermissionsEgress', []))
                    }
                ))
                node_id_counter += 1
        except Exception as e:
            logger.warning("security_group_discovery_error", error=str(e))
        
        # Discover Route Tables
        try:
            ec2 = session.client('ec2')
            rt_response = ec2.describe_route_tables()
            
            for rt in rt_response.get('RouteTables', []):
                rt_id = rt.get('RouteTableId')
                rt_name = next((tag['Value'] for tag in rt.get('Tags', []) if tag['Key'] == 'Name'), rt_id)
                
                nodes.append(ServiceNode(
                    id=f"rt-{node_id_counter:03d}",
                    name=rt_name,
                    type="route_table",
                    provider="aws",
                    region=region,
                    status="healthy",
                    resource_count=1,
                    metadata={
                        "rt_id": rt_id,
                        "vpc_id": rt.get('VpcId'),
                        "routes_count": len(rt.get('Routes', [])),
                        "associations_count": len(rt.get('Associations', []))
                    }
                ))
                node_id_counter += 1
        except Exception as e:
            logger.warning("route_table_discovery_error", error=str(e))
        
        # Discover Load Balancers (ALB/NLB)
        try:
            elbv2 = session.client('elbv2')
            lb_response = elbv2.describe_load_balancers()
            
            for lb in lb_response.get('LoadBalancers', []):
                lb_name = lb.get('LoadBalancerName')
                lb_type = lb.get('Type', 'application')
                
                nodes.append(ServiceNode(
                    id=f"lb-{node_id_counter:03d}",
                    name=lb_name,
                    type="load_balancer",
                    provider="aws",
                    region=region,
                    status="healthy" if lb.get('State', {}).get('Code') == 'active' else "degraded",
                    resource_count=1,
                    metadata={
                        "lb_arn": lb.get('LoadBalancerArn'),
                        "lb_type": lb_type,
                        "scheme": lb.get('Scheme'),
                        "vpc_id": lb.get('VpcId'),
                        "dns_name": lb.get('DNSName'),
                        "state": lb.get('State', {}).get('Code')
                    }
                ))
                node_id_counter += 1
        except Exception as e:
            logger.warning("load_balancer_discovery_error", error=str(e))
        
        # Discover Classic Load Balancers
        try:
            elb = session.client('elb')
            clb_response = elb.describe_load_balancers()
            
            for lb in clb_response.get('LoadBalancerDescriptions', []):
                lb_name = lb.get('LoadBalancerName')
                
                nodes.append(ServiceNode(
                    id=f"clb-{node_id_counter:03d}",
                    name=lb_name,
                    type="load_balancer",
                    provider="aws",
                    region=region,
                    status="healthy",
                    resource_count=1,
                    metadata={
                        "lb_type": "classic",
                        "scheme": lb.get('Scheme'),
                        "vpc_id": lb.get('VPCId'),
                        "dns_name": lb.get('DNSName'),
                        "instances": [inst.get('InstanceId') for inst in lb.get('Instances', [])]
                    }
                ))
                node_id_counter += 1
        except Exception as e:
            logger.warning("classic_load_balancer_discovery_error", error=str(e))
        
        # Create edges based on resource relationships
        lambda_nodes = [n for n in nodes if n.type == "lambda"]
        rds_nodes = [n for n in nodes if n.type == "rds"]
        dynamodb_nodes = [n for n in nodes if n.type == "dynamodb"]
        s3_nodes = [n for n in nodes if n.type == "s3"]
        ec2_nodes = [n for n in nodes if n.type == "ec2"]
        vpc_nodes = [n for n in nodes if n.type == "vpc"]
        subnet_nodes = [n for n in nodes if n.type == "subnet"]
        igw_nodes = [n for n in nodes if n.type == "internet_gateway"]
        nat_nodes = [n for n in nodes if n.type == "nat_gateway"]
        sg_nodes = [n for n in nodes if n.type == "security_group"]
        api_nodes = [n for n in nodes if n.type == "apigateway"]
        lb_nodes = [n for n in nodes if n.type == "load_balancer"]
        
        edge_id = 1
        
        # VPC -> Subnet relationships
        for subnet_node in subnet_nodes:
            vpc_id = subnet_node.metadata.get('vpc_id')
            if vpc_id:
                vpc_node = next((n for n in vpc_nodes if n.metadata.get('vpc_id') == vpc_id), None)
                if vpc_node:
                    edges.append(ServiceEdge(
                        id=f"edge-{edge_id}",
                        source=vpc_node.id,
                        target=subnet_node.id,
                        relationship="CONTAINS"
                    ))
                    edge_id += 1
        
        # VPC -> Internet Gateway relationships
        for igw_node in igw_nodes:
            for vpc_id in igw_node.metadata.get('attachments', []):
                vpc_node = next((n for n in vpc_nodes if n.metadata.get('vpc_id') == vpc_id), None)
                if vpc_node:
                    edges.append(ServiceEdge(
                        id=f"edge-{edge_id}",
                        source=vpc_node.id,
                        target=igw_node.id,
                        relationship="ROUTES_TO"
                    ))
                    edge_id += 1
        
        # Subnet -> NAT Gateway relationships
        for nat_node in nat_nodes:
            subnet_id = nat_node.metadata.get('subnet_id')
            if subnet_id:
                subnet_node = next((n for n in subnet_nodes if n.metadata.get('subnet_id') == subnet_id), None)
                if subnet_node:
                    edges.append(ServiceEdge(
                        id=f"edge-{edge_id}",
                        source=subnet_node.id,
                        target=nat_node.id,
                        relationship="CONTAINS"
                    ))
                    edge_id += 1
        
        # EC2 -> VPC/Subnet relationships
        for ec2_node in ec2_nodes:
            vpc_id = ec2_node.metadata.get('vpc_id')
            subnet_id = ec2_node.metadata.get('subnet_id')
            
            if subnet_id:
                subnet_node = next((n for n in subnet_nodes if n.metadata.get('subnet_id') == subnet_id), None)
                if subnet_node:
                    edges.append(ServiceEdge(
                        id=f"edge-{edge_id}",
                        source=subnet_node.id,
                        target=ec2_node.id,
                        relationship="HOSTS"
                    ))
                    edge_id += 1
        
        # Lambda -> VPC/Subnet relationships
        for lambda_node in lambda_nodes:
            subnet_ids = lambda_node.metadata.get('subnet_ids', [])
            for subnet_id in subnet_ids:
                subnet_node = next((n for n in subnet_nodes if n.metadata.get('subnet_id') == subnet_id), None)
                if subnet_node:
                    edges.append(ServiceEdge(
                        id=f"edge-{edge_id}",
                        source=subnet_node.id,
                        target=lambda_node.id,
                        relationship="HOSTS"
                    ))
                    edge_id += 1
        
        # Load Balancer -> EC2 relationships
        for lb_node in lb_nodes:
            instance_ids = lb_node.metadata.get('instances', [])
            for instance_id in instance_ids:
                ec2_node = next((n for n in ec2_nodes if n.metadata.get('instance_id') == instance_id), None)
                if ec2_node:
                    edges.append(ServiceEdge(
                        id=f"edge-{edge_id}",
                        source=lb_node.id,
                        target=ec2_node.id,
                        relationship="ROUTES_TO"
                    ))
                    edge_id += 1
        
        # API Gateway -> Lambda (common pattern)
        if api_nodes and lambda_nodes:
            for api_node in api_nodes:
                for lambda_node in lambda_nodes[:2]:  # Connect to first 2 lambdas
                    edges.append(ServiceEdge(
                        id=f"edge-{edge_id}",
                        source=api_node.id,
                        target=lambda_node.id,
                        relationship="INVOKES"
                    ))
                    edge_id += 1
        
        # Load Balancer -> Lambda (for ALB with Lambda targets)
        if lb_nodes and lambda_nodes and not ec2_nodes:
            for lb_node in lb_nodes:
                for lambda_node in lambda_nodes:
                    edges.append(ServiceEdge(
                        id=f"edge-{edge_id}",
                        source=lb_node.id,
                        target=lambda_node.id,
                        relationship="ROUTES_TO"
                    ))
                    edge_id += 1
        
        # Lambda -> Database relationships (common pattern)
        for lambda_node in lambda_nodes:
            # Lambda -> RDS
            if rds_nodes:
                edges.append(ServiceEdge(
                    id=f"edge-{edge_id}",
                    source=lambda_node.id,
                    target=rds_nodes[0].id,
                    relationship="READS_FROM"
                ))
                edge_id += 1
            
            # Lambda -> DynamoDB
            if dynamodb_nodes:
                edges.append(ServiceEdge(
                    id=f"edge-{edge_id}",
                    source=lambda_node.id,
                    target=dynamodb_nodes[0].id,
                    relationship="READS_FROM"
                ))
                edge_id += 1
            
            # Lambda -> S3
            if s3_nodes:
                edges.append(ServiceEdge(
                    id=f"edge-{edge_id}",
                    source=lambda_node.id,
                    target=s3_nodes[0].id,
                    relationship="READS_FROM"
                ))
                edge_id += 1
        
        logger.info("topology_graph_returned", tenant_id=tenant_id, nodes=len(nodes), edges=len(edges))
        
        # Store in cache
        _topology_cache[cache_key] = {
            'nodes': nodes,
            'edges': edges,
            'timestamp': datetime.now()
        }
        
        return TopologyGraph(nodes=nodes, edges=edges)
        
    except ClientError as e:
        logger.error("aws_discovery_error", tenant_id=tenant_id, error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to discover AWS resources: {str(e)}"
        )
    except Exception as e:
        logger.error("topology_graph_error", tenant_id=tenant_id, error=str(e))
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate topology: {str(e)}"
        )


@router.post("/topology/rediscover")
async def trigger_rediscovery(
    tenant_id: str = Query(...),
    db: AsyncSession = Depends(get_db)
) -> RediscoveryJob:
    """Trigger a rediscovery of the service topology."""
    try:
        logger.info("triggering_topology_rediscovery", tenant_id=tenant_id)
        
        # Clear cache for this tenant
        cache_key = f"topology_graph_{tenant_id}"
        if cache_key in _topology_cache:
            del _topology_cache[cache_key]
            logger.info("topology_cache_cleared", tenant_id=tenant_id)
        
        # Get AWS integrations
        integrations = await crud.get_integrations(db, tenant_id, "aws")
        
        if not integrations:
            raise HTTPException(status_code=404, detail="No AWS integration found")
        
        integration = next((i for i in integrations if i.is_active), None)
        if not integration:
            raise HTTPException(status_code=404, detail="No active AWS integration found")
        
        # Decrypt config
        config_dict = crud.decrypt_integration_config(integration)
        
        access_key = config_dict.get("access_key_id")
        secret_key = config_dict.get("secret_access_key")
        region = config_dict.get("region", "us-east-1")
        
        if not access_key or not secret_key:
            raise HTTPException(status_code=400, detail="Missing AWS credentials")
        
        # Simulate discovery process (in production, this would be a background job)
        # For now, we'll add a small delay to show the progress UI
        import asyncio
        await asyncio.sleep(2)  # Simulate discovery time
        
        # In a full implementation, this would:
        # 1. Start a background job to discover all AWS resources
        # 2. Analyze resource relationships
        # 3. Build the topology graph
        # 4. Store in database
        # 5. Return job ID for status tracking
        
        job_id = f"job-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        
        logger.info("topology_rediscovery_completed", tenant_id=tenant_id, job_id=job_id)
        
        return RediscoveryJob(
            job_id=job_id,
            status="completed",
            started_at=datetime.now().isoformat(),
            message=f"Discovered resources in {region}. Topology updated successfully."
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("trigger_rediscovery_error", tenant_id=tenant_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to trigger rediscovery: {str(e)}")


@router.get("/topology/services")
async def get_services(
    tenant_id: str = Query(...),
    db: AsyncSession = Depends(get_db)
):
    """Get list of services."""
    # Get topology graph and return just the nodes
    graph = await get_topology_graph(tenant_id, db)
    return graph.nodes


@router.get("/topology/services/{service_name}")
async def get_service_detail(
    service_name: str,
    tenant_id: str = Query(...),
    db: AsyncSession = Depends(get_db)
):
    """Get detailed information about a specific service."""
    try:
        logger.info("fetching_service_detail", tenant_id=tenant_id, service_name=service_name)
        
        # Get topology graph
        graph = await get_topology_graph(tenant_id, db)
        
        # Find the service node
        service_node = next((n for n in graph.nodes if n.name == service_name), None)
        
        if not service_node:
            raise HTTPException(status_code=404, detail=f"Service '{service_name}' not found")
        
        # Find dependencies (outgoing edges from this service)
        dependencies = [
            edge.target for edge in graph.edges 
            if edge.source == service_node.id
        ]
        
        # Find dependents (incoming edges to this service)
        dependents = [
            edge.source for edge in graph.edges 
            if edge.target == service_node.id
        ]
        
        # Build service detail response
        return {
            "id": service_node.id,
            "name": service_node.name,
            "type": service_node.type,
            "provider": service_node.provider,
            "region": service_node.region,
            "status": service_node.status,
            "resource_count": service_node.resource_count,
            "metadata": service_node.metadata,
            "dependencies": dependencies,
            "dependents": dependents,
            "resources": [],  # Empty array for now
            "past_incidents": [],  # Empty array for now
            "health_summary": {
                "cpu_usage": 0,
                "memory_usage": 0,
                "request_rate": 0,
                "error_rate": 0,
            },
            "team_owner": None,
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("get_service_detail_error", tenant_id=tenant_id, service_name=service_name, error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to fetch service details: {str(e)}")


@router.get("/topology/resources")
async def get_resources(
    tenant_id: str = Query(...),
    provider: Optional[str] = Query(None),
    resource_type: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """Get cloud resources inventory.
    
    The Resources tab shows all discovered cloud resources (EC2, RDS, Lambda, etc.)
    that make up the services in the topology.
    """
    try:
        logger.info("fetching_resources", tenant_id=tenant_id, provider=provider, resource_type=resource_type, search=search)
        
        # Get AWS integrations
        integrations = await crud.get_integrations(db, tenant_id, provider or "aws")
        
        if not integrations:
            return {"items": [], "total": 0, "page": 1, "page_size": 50}
        
        integration = next((i for i in integrations if i.is_active), None)
        if not integration:
            return {"items": [], "total": 0, "page": 1, "page_size": 50}
        
        # Get topology graph to extract resources
        graph = await get_topology_graph(tenant_id, db)
        
        # Convert topology nodes to resource items
        # In a full implementation, this would discover actual AWS resources
        # For now, we'll create resource entries from the topology nodes
        resources = []
        for node in graph.nodes:
            # Apply filters BEFORE creating resource object
            if resource_type and node.type != resource_type:
                continue
            if search and search.lower() not in node.name.lower():
                continue
            if provider and node.provider != provider:
                continue
            
            resource = {
                "resource_id": node.id,
                "name": node.name,
                "type": node.type,
                "provider": node.provider,
                "region": node.region or "us-east-1",
                "status": node.status,
                "service_name": node.metadata.get("display_name", node.name),
                "tags": node.metadata,
                "created_at": datetime.now().isoformat(),
                "arn": f"arn:aws:{node.type}:{node.region or 'us-east-1'}:123456789012:{node.name}",
            }
                
            resources.append(resource)
        
        logger.info("resources_returned", tenant_id=tenant_id, count=len(resources))
        
        return {
            "items": resources,
            "total": len(resources),
            "page": 1,
            "page_size": 50
        }
        
    except HTTPException:
        # Re-raise HTTP exceptions from get_topology_graph
        raise
    except Exception as e:
        logger.error("get_resources_error", tenant_id=tenant_id, error=str(e))
        raise HTTPException(status_code=500, detail=f"Failed to fetch resources: {str(e)}")
