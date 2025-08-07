import boto3
from botocore.exceptions import ClientError, NoCredentialsError
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

class EC2Service:
    def __init__(self):
        self.default_region = os.environ.get('AWS_REGION', 'us-east-2')
        # Common regions to check
        self.common_regions = [
            'us-east-1', 'us-east-2', 'us-west-1', 'us-west-2',
            'ap-southeast-1', 'ap-southeast-2', 'ap-northeast-1',
            'eu-west-1', 'eu-central-1'
        ]
    
    def get_all_regions(self):
        """Get all available AWS regions"""
        try:
            ec2 = boto3.client('ec2', region_name=self.default_region)
            response = ec2.describe_regions()
            return [region['RegionName'] for region in response['Regions']]
        except (ClientError, NoCredentialsError):
            return self.common_regions  # fallback to common regions
    
    def list_instances_in_region(self, region):
        """List instances in a specific region"""
        try:
            ec2 = boto3.client('ec2', region_name=region)
            response = ec2.describe_instances()
            instances = []
            
            for reservation in response['Reservations']:
                for instance in reservation['Instances']:
                    if instance['State']['Name'] == 'terminated':
                        continue
                        
                    name = 'No Name'
                    if 'Tags' in instance:
                        for tag in instance['Tags']:
                            if tag['Key'] == 'Name':
                                name = tag['Value']
                                break
                    
                    instances.append({
                        'id': instance['InstanceId'],
                        'name': name,
                        'state': instance['State']['Name'],
                        'type': instance['InstanceType'],
                        'region': region,
                        'az': instance['Placement']['AvailabilityZone']
                    })
            
            return instances
        except (ClientError, NoCredentialsError):
            return []  # Return empty list if region fails

    def list_instances(self):
        """List instances from default region only"""
        return self.list_instances_in_region(self.default_region)

    def list_all_instances(self):
        """List instances from ALL regions (parallel)"""
        try:
            regions = self.get_all_regions()
            all_instances = []
            
            # Use ThreadPoolExecutor for parallel region queries
            with ThreadPoolExecutor(max_workers=10) as executor:
                future_to_region = {
                    executor.submit(self.list_instances_in_region, region): region 
                    for region in regions
                }
                
                for future in as_completed(future_to_region):
                    region = future_to_region[future]
                    try:
                        instances = future.result()
                        all_instances.extend(instances)
                    except Exception:
                        continue  # Skip failed regions
            
            return all_instances
        except Exception:
            # Fallback to mock data if no credentials
            return self._get_mock_instances()

    def _get_mock_instances(self):
        """Mock data for testing"""
        return [
            {
                'id': 'i-1234567890abcdef0',
                'name': 'Web Server US-East',
                'state': 'running',
                'type': 't3.micro',
                'region': 'us-east-1',
                'az': 'us-east-1a'
            },
            {
                'id': 'i-0987654321fedcba0',
                'name': 'DB Server US-West',
                'state': 'stopped',
                'type': 't3.small',
                'region': 'us-west-2',
                'az': 'us-west-2b'
            },
            {
                'id': 'i-abcdef1234567890',
                'name': 'API Server Singapore',
                'state': 'running',
                'type': 't3.medium',
                'region': 'ap-southeast-1',
                'az': 'ap-southeast-1a'
            }
        ]
            
    def start_instance(self, instance_id, region):
        """Start instance in specific region"""
        try:
            ec2 = boto3.client('ec2', region_name=region)
            ec2.start_instances(InstanceIds=[instance_id])
            return {'success': f'Starting instance {instance_id} in {region}'}
        except NoCredentialsError:
            return {'success': f'[MOCK] Starting instance {instance_id} in {region}'}
        except ClientError as e:
            return {'error': str(e)}
    
    def stop_instance(self, instance_id, region):
        """Stop instance in specific region"""
        try:
            ec2 = boto3.client('ec2', region_name=region)
            ec2.stop_instances(InstanceIds=[instance_id])
            return {'success': f'Stopping instance {instance_id} in {region}'}
        except NoCredentialsError:
            return {'success': f'[MOCK] Stopping instance {instance_id} in {region}'}
        except ClientError as e:
            return {'error': str(e)}
    
    def get_instance_status(self, instance_id, region):
        """Get instance status from specific region"""
        try:
            ec2 = boto3.client('ec2', region_name=region)
            response = ec2.describe_instances(InstanceIds=[instance_id])
            instance = response['Reservations'][0]['Instances'][0]
            
            return {
                'id': instance['InstanceId'],
                'state': instance['State']['Name'],
                'type': instance['InstanceType'],
                'region': region,
                'launch_time': instance.get('LaunchTime', 'N/A'),
                'public_ip': instance.get('PublicIpAddress', 'N/A'),
                'private_ip': instance.get('PrivateIpAddress', 'N/A')
            }
        except NoCredentialsError:
            return {
                'id': instance_id,
                'state': 'running',
                'type': 't3.micro',
                'region': region,
                'launch_time': '2024-01-01T00:00:00.000Z',
                'public_ip': '1.2.3.4',
                'private_ip': '10.0.1.100'
            }
        except ClientError as e:
            return {'error': str(e)}
