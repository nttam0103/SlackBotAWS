import boto3
from botocore.exceptions import ClientError
import os

class EC2Service:
    def __init__(self):
        self.ec2 = boto3.client(
            'ec2',
            region_name=os.environ.get('AWS_REGION', 'us-east-2'),
        )
    
    def list_instances(self):
        try:
            response = self.ec2.describe_instances()
            instances = []
            
            for reservation in response['Reservations']:
                for instance in reservation['Instances']:
                    # Skip terminated instances
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
                        'az': instance['Placement']['AvailabilityZone']
                    })
            
            return instances
        except ClientError as e:
            return {'error': str(e)}
    
    def start_instance(self, instance_id):
        try:
            self.ec2.start_instances(InstanceIds=[instance_id])
            return {'success': f'Starting instance {instance_id}'}
        except ClientError as e:
            return {'error': str(e)}
    
    def stop_instance(self, instance_id):
        try:
            self.ec2.stop_instances(InstanceIds=[instance_id])
            return {'success': f'Stopping instance {instance_id}'}
        except ClientError as e:
            return {'error': str(e)}
    
    def get_instance_status(self, instance_id):
        try:
            response = self.ec2.describe_instances(InstanceIds=[instance_id])
            instance = response['Reservations'][0]['Instances'][0]
            
            return {
                'id': instance['InstanceId'],
                'state': instance['State']['Name'],
                'type': instance['InstanceType'],
                'launch_time': instance.get('LaunchTime', 'N/A'),
                'public_ip': instance.get('PublicIpAddress', 'N/A'),
                'private_ip': instance.get('PrivateIpAddress', 'N/A')
            }
        except ClientError as e:
            return {'error': str(e)}
