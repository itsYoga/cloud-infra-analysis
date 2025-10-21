"""
真實 AWS 資料提取器

這個模組使用 boto3 來提取真實的 AWS 資源資料。
需要有效的 AWS 認證才能使用。
"""

import boto3
import json
import logging
from datetime import datetime
from typing import Dict, List, Any, Optional

logger = logging.getLogger(__name__)


class AWSExtractor:
    """AWS 資料提取器"""
    
    def __init__(self, region: str = 'us-east-1'):
        self.region = region
        self.session = None
        self._initialize_session()
    
    def _initialize_session(self):
        """初始化 AWS 會話"""
        try:
            self.session = boto3.Session(region_name=self.region)
            # 測試連接
            sts = self.session.client('sts')
            identity = sts.get_caller_identity()
            logger.info(f"成功連接到 AWS，帳戶 ID: {identity.get('Account')}")
            logger.info(f"使用者 ARN: {identity.get('Arn')}")
        except Exception as e:
            logger.error(f"AWS 連接失敗: {e}")
            raise
    
    def extract_ec2_instances(self) -> Dict[str, Any]:
        """提取 EC2 實例"""
        try:
            ec2 = self.session.client('ec2')
            response = ec2.describe_instances()
            
            instances = []
            for reservation in response['Reservations']:
                for instance in reservation['Instances']:
                    instance_data = {
                        'InstanceId': instance['InstanceId'],
                        'InstanceType': instance['InstanceType'],
                        'State': instance['State']['Name'],
                        'LaunchTime': instance['LaunchTime'].isoformat(),
                        'VpcId': instance.get('VpcId'),
                        'SubnetId': instance.get('SubnetId'),
                        'PublicIpAddress': instance.get('PublicIpAddress'),
                        'PrivateIpAddress': instance.get('PrivateIpAddress'),
                        'SecurityGroups': instance.get('SecurityGroups', []),
                        'Tags': instance.get('Tags', []),
                        'Placement': {
                            'AvailabilityZone': instance.get('Placement', {}).get('AvailabilityZone')
                        }
                    }
                    instances.append(instance_data)
            
            return {
                'Reservations': [{
                    'ReservationId': f'r-{datetime.now().strftime("%Y%m%d%H%M%S")}',
                    'OwnerId': self.session.client('sts').get_caller_identity()['Account'],
                    'Groups': [],
                    'Instances': instances
                }]
            }
            
        except Exception as e:
            logger.error(f"提取 EC2 實例失敗: {e}")
            return {'Reservations': []}
    
    def extract_security_groups(self) -> Dict[str, Any]:
        """提取安全群組"""
        try:
            ec2 = self.session.client('ec2')
            response = ec2.describe_security_groups()
            
            return {
                'SecurityGroups': response['SecurityGroups']
            }
            
        except Exception as e:
            logger.error(f"提取安全群組失敗: {e}")
            return {'SecurityGroups': []}
    
    def extract_vpcs(self) -> Dict[str, Any]:
        """提取 VPC"""
        try:
            ec2 = self.session.client('ec2')
            response = ec2.describe_vpcs()
            
            return {
                'Vpcs': response['Vpcs']
            }
            
        except Exception as e:
            logger.error(f"提取 VPC 失敗: {e}")
            return {'Vpcs': []}
    
    def extract_subnets(self) -> Dict[str, Any]:
        """提取子網路"""
        try:
            ec2 = self.session.client('ec2')
            response = ec2.describe_subnets()
            
            return {
                'Subnets': response['Subnets']
            }
            
        except Exception as e:
            logger.error(f"提取子網路失敗: {e}")
            return {'Subnets': []}
    
    def extract_ebs_volumes(self) -> Dict[str, Any]:
        """提取 EBS 磁碟"""
        try:
            ec2 = self.session.client('ec2')
            response = ec2.describe_volumes()
            
            return {
                'Volumes': response['Volumes']
            }
            
        except Exception as e:
            logger.error(f"提取 EBS 磁碟失敗: {e}")
            return {'Volumes': []}
    
    def extract_rds_instances(self) -> Dict[str, Any]:
        """提取 RDS 實例"""
        try:
            rds = self.session.client('rds')
            response = rds.describe_db_instances()
            
            return {
                'DBInstances': response['DBInstances']
            }
            
        except Exception as e:
            logger.error(f"提取 RDS 實例失敗: {e}")
            return {'DBInstances': []}
    
    def extract_load_balancers(self) -> Dict[str, Any]:
        """提取負載平衡器"""
        try:
            elbv2 = self.session.client('elbv2')
            response = elbv2.describe_load_balancers()
            
            return {
                'LoadBalancers': response['LoadBalancers']
            }
            
        except Exception as e:
            logger.error(f"提取負載平衡器失敗: {e}")
            return {'LoadBalancers': []}
    
    def extract_s3_buckets(self) -> Dict[str, Any]:
        """提取 S3 儲存桶"""
        try:
            s3 = self.session.client('s3')
            response = s3.list_buckets()
            
            return {
                'Buckets': response['Buckets'],
                'Owner': response['Owner']
            }
            
        except Exception as e:
            logger.error(f"提取 S3 儲存桶失敗: {e}")
            return {'Buckets': [], 'Owner': {}}
    
    def extract_lambda_functions(self) -> Dict[str, Any]:
        """提取 Lambda 函數"""
        try:
            lambda_client = self.session.client('lambda')
            response = lambda_client.list_functions()
            
            return {
                'Functions': response['Functions']
            }
            
        except Exception as e:
            logger.error(f"提取 Lambda 函數失敗: {e}")
            return {'Functions': []}
    
    def extract_all_resources(self) -> Dict[str, Any]:
        """提取所有 AWS 資源"""
        logger.info("開始提取真實 AWS 資源...")
        
        resources = {
            'metadata': {
                'extraction_time': datetime.now().isoformat(),
                'region': self.region,
                'data_type': 'real_aws_data'
            },
            'ec2_instances': self.extract_ec2_instances(),
            'security_groups': self.extract_security_groups(),
            'vpcs': self.extract_vpcs(),
            'subnets': self.extract_subnets(),
            'ebs_volumes': self.extract_ebs_volumes(),
            'rds_instances': self.extract_rds_instances(),
            'load_balancers': self.extract_load_balancers(),
            's3_buckets': self.extract_s3_buckets(),
            'lambda_functions': self.extract_lambda_functions()
        }
        
        logger.info("AWS 資源提取完成")
        return resources
