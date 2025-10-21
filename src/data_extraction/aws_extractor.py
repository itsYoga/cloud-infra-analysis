"""
AWS 雲端資源資料擷取器

本模組負責從 AWS 擷取各種雲端資源的設定資料，
包括 EC2、VPC、安全群組、S3 等資源的詳細資訊。
"""

import boto3
import json
import os
from datetime import datetime
from typing import Dict, List, Any, Optional
from loguru import logger
from botocore.exceptions import ClientError, NoCredentialsError


class AWSExtractor:
    """AWS 資源擷取器"""
    
    def __init__(self, region: str = "us-east-1", profile: Optional[str] = None):
        """
        初始化 AWS 擷取器
        
        Args:
            region: AWS 區域
            profile: AWS 設定檔名稱
        """
        self.region = region
        self.profile = profile
        self.session = self._create_session()
        self.resources = {}
        
    def _create_session(self) -> boto3.Session:
        """創建 AWS 會話"""
        try:
            if self.profile:
                session = boto3.Session(profile_name=self.profile)
            else:
                session = boto3.Session()
            
            # 測試憑證
            sts = session.client('sts')
            sts.get_caller_identity()
            logger.info(f"成功連接到 AWS，區域: {self.region}")
            return session
            
        except NoCredentialsError:
            logger.error("未找到 AWS 憑證，請設定 AWS_ACCESS_KEY_ID 和 AWS_SECRET_ACCESS_KEY")
            raise
        except Exception as e:
            logger.error(f"連接 AWS 失敗: {e}")
            raise
    
    def extract_all_resources(self) -> Dict[str, Any]:
        """擷取所有 AWS 資源"""
        logger.info("開始擷取 AWS 資源...")
        
        try:
            # 擷取各種資源
            self.resources = {
                'metadata': {
                    'extraction_time': datetime.now().isoformat(),
                    'region': self.region,
                    'account_id': self._get_account_id()
                },
                'ec2_instances': self._extract_ec2_instances(),
                'security_groups': self._extract_security_groups(),
                'vpcs': self._extract_vpcs(),
                'subnets': self._extract_subnets(),
                'load_balancers': self._extract_load_balancers(),
                's3_buckets': self._extract_s3_buckets(),
                'ebs_volumes': self._extract_ebs_volumes(),
                'rds_instances': self._extract_rds_instances(),
                'lambda_functions': self._extract_lambda_functions()
            }
            
            logger.info("AWS 資源擷取完成")
            return self.resources
            
        except Exception as e:
            logger.error(f"擷取 AWS 資源時發生錯誤: {e}")
            raise
    
    def _get_account_id(self) -> str:
        """獲取 AWS 帳戶 ID"""
        try:
            sts = self.session.client('sts')
            return sts.get_caller_identity()['Account']
        except Exception as e:
            logger.warning(f"無法獲取帳戶 ID: {e}")
            return "unknown"
    
    def _extract_ec2_instances(self) -> List[Dict[str, Any]]:
        """擷取 EC2 實例"""
        logger.info("擷取 EC2 實例...")
        ec2 = self.session.client('ec2', region_name=self.region)
        
        try:
            response = ec2.describe_instances()
            instances = []
            
            for reservation in response['Reservations']:
                for instance in reservation['Instances']:
                    instance_data = {
                        'InstanceID': instance['InstanceId'],
                        'Name': self._get_tag_value(instance.get('Tags', []), 'Name', instance['InstanceId']),
                        'State': instance['State']['Name'],
                        'InstanceType': instance['InstanceType'],
                        'PublicIP': instance.get('PublicIpAddress'),
                        'PrivateIP': instance.get('PrivateIpAddress'),
                        'LaunchTime': instance['LaunchTime'].isoformat() if 'LaunchTime' in instance else None,
                        'Region': self.region,
                        'AZ': instance.get('Placement', {}).get('AvailabilityZone'),
                        'SecurityGroups': [sg['GroupId'] for sg in instance.get('SecurityGroups', [])],
                        'SubnetId': instance.get('SubnetId'),
                        'VpcId': instance.get('VpcId'),
                        'Tags': instance.get('Tags', [])
                    }
                    instances.append(instance_data)
            
            logger.info(f"擷取到 {len(instances)} 個 EC2 實例")
            return instances
            
        except ClientError as e:
            logger.error(f"擷取 EC2 實例失敗: {e}")
            return []
    
    def _extract_security_groups(self) -> List[Dict[str, Any]]:
        """擷取安全群組"""
        logger.info("擷取安全群組...")
        ec2 = self.session.client('ec2', region_name=self.region)
        
        try:
            response = ec2.describe_security_groups()
            security_groups = []
            
            for sg in response['SecurityGroups']:
                sg_data = {
                    'GroupID': sg['GroupId'],
                    'GroupName': sg['GroupName'],
                    'VpcId': sg['VpcId'],
                    'Description': sg['Description'],
                    'Region': self.region,
                    'Rules': []
                }
                
                # 擷取入站規則
                for rule in sg.get('IpPermissions', []):
                    rule_data = {
                        'RuleID': f"{sg['GroupId']}-in-{rule.get('IpProtocol', 'tcp')}-{rule.get('FromPort', 0)}",
                        'Protocol': rule.get('IpProtocol', 'tcp'),
                        'PortRange': f"{rule.get('FromPort', 0)}-{rule.get('ToPort', 0)}",
                        'SourceCIDR': ', '.join([ip['CidrIp'] for ip in rule.get('IpRanges', [])]),
                        'Direction': 'inbound',
                        'Action': 'allow',
                        'Description': rule.get('Description', '')
                    }
                    sg_data['Rules'].append(rule_data)
                
                # 擷取出站規則
                for rule in sg.get('IpPermissionsEgress', []):
                    rule_data = {
                        'RuleID': f"{sg['GroupId']}-out-{rule.get('IpProtocol', 'tcp')}-{rule.get('FromPort', 0)}",
                        'Protocol': rule.get('IpProtocol', 'tcp'),
                        'PortRange': f"{rule.get('FromPort', 0)}-{rule.get('ToPort', 0)}",
                        'SourceCIDR': ', '.join([ip['CidrIp'] for ip in rule.get('IpRanges', [])]),
                        'Direction': 'outbound',
                        'Action': 'allow',
                        'Description': rule.get('Description', '')
                    }
                    sg_data['Rules'].append(rule_data)
                
                security_groups.append(sg_data)
            
            logger.info(f"擷取到 {len(security_groups)} 個安全群組")
            return security_groups
            
        except ClientError as e:
            logger.error(f"擷取安全群組失敗: {e}")
            return []
    
    def _extract_vpcs(self) -> List[Dict[str, Any]]:
        """擷取 VPC"""
        logger.info("擷取 VPC...")
        ec2 = self.session.client('ec2', region_name=self.region)
        
        try:
            response = ec2.describe_vpcs()
            vpcs = []
            
            for vpc in response['Vpcs']:
                vpc_data = {
                    'VpcId': vpc['VpcId'],
                    'CidrBlock': vpc['CidrBlock'],
                    'State': vpc['State'],
                    'Name': self._get_tag_value(vpc.get('Tags', []), 'Name', vpc['VpcId']),
                    'Region': self.region,
                    'IsDefault': vpc['IsDefault']
                }
                vpcs.append(vpc_data)
            
            logger.info(f"擷取到 {len(vpcs)} 個 VPC")
            return vpcs
            
        except ClientError as e:
            logger.error(f"擷取 VPC 失敗: {e}")
            return []
    
    def _extract_subnets(self) -> List[Dict[str, Any]]:
        """擷取子網路"""
        logger.info("擷取子網路...")
        ec2 = self.session.client('ec2', region_name=self.region)
        
        try:
            response = ec2.describe_subnets()
            subnets = []
            
            for subnet in response['Subnets']:
                subnet_data = {
                    'SubnetId': subnet['SubnetId'],
                    'CidrBlock': subnet['CidrBlock'],
                    'AvailabilityZone': subnet['AvailabilityZone'],
                    'Name': self._get_tag_value(subnet.get('Tags', []), 'Name', subnet['SubnetId']),
                    'State': subnet['State'],
                    'VpcId': subnet['VpcId'],
                    'Region': self.region
                }
                subnets.append(subnet_data)
            
            logger.info(f"擷取到 {len(subnets)} 個子網路")
            return subnets
            
        except ClientError as e:
            logger.error(f"擷取子網路失敗: {e}")
            return []
    
    def _extract_load_balancers(self) -> List[Dict[str, Any]]:
        """擷取負載平衡器"""
        logger.info("擷取負載平衡器...")
        elbv2 = self.session.client('elbv2', region_name=self.region)
        
        try:
            response = elbv2.describe_load_balancers()
            load_balancers = []
            
            for lb in response['LoadBalancers']:
                lb_data = {
                    'LoadBalancerName': lb['LoadBalancerName'],
                    'DNSName': lb['DNSName'],
                    'State': lb['State']['Code'],
                    'Scheme': lb['Scheme'],
                    'Type': lb['Type'],
                    'VpcId': lb['VpcId'],
                    'Region': self.region,
                    'CreatedTime': lb['CreatedTime'].isoformat()
                }
                load_balancers.append(lb_data)
            
            logger.info(f"擷取到 {len(load_balancers)} 個負載平衡器")
            return load_balancers
            
        except ClientError as e:
            logger.error(f"擷取負載平衡器失敗: {e}")
            return []
    
    def _extract_s3_buckets(self) -> List[Dict[str, Any]]:
        """擷取 S3 儲存桶"""
        logger.info("擷取 S3 儲存桶...")
        s3 = self.session.client('s3', region_name=self.region)
        
        try:
            response = s3.list_buckets()
            buckets = []
            
            for bucket in response['Buckets']:
                bucket_data = {
                    'BucketName': bucket['Name'],
                    'CreationDate': bucket['CreationDate'].isoformat(),
                    'Region': self.region
                }
                
                # 嘗試獲取額外資訊
                try:
                    location_response = s3.get_bucket_location(Bucket=bucket['Name'])
                    bucket_data['Location'] = location_response.get('LocationConstraint', 'us-east-1')
                except:
                    bucket_data['Location'] = 'unknown'
                
                buckets.append(bucket_data)
            
            logger.info(f"擷取到 {len(buckets)} 個 S3 儲存桶")
            return buckets
            
        except ClientError as e:
            logger.error(f"擷取 S3 儲存桶失敗: {e}")
            return []
    
    def _extract_ebs_volumes(self) -> List[Dict[str, Any]]:
        """擷取 EBS 磁碟"""
        logger.info("擷取 EBS 磁碟...")
        ec2 = self.session.client('ec2', region_name=self.region)
        
        try:
            response = ec2.describe_volumes()
            volumes = []
            
            for volume in response['Volumes']:
                volume_data = {
                    'VolumeId': volume['VolumeId'],
                    'Size': volume['Size'],
                    'VolumeType': volume['VolumeType'],
                    'State': volume['State'],
                    'CreationDate': volume['CreateTime'].isoformat(),
                    'Encrypted': volume['Encrypted'],
                    'Iops': volume.get('Iops'),
                    'Region': self.region,
                    'Attachments': [
                        {
                            'InstanceId': att['InstanceId'],
                            'Device': att['Device'],
                            'AttachTime': att['AttachTime'].isoformat()
                        } for att in volume.get('Attachments', [])
                    ]
                }
                volumes.append(volume_data)
            
            logger.info(f"擷取到 {len(volumes)} 個 EBS 磁碟")
            return volumes
            
        except ClientError as e:
            logger.error(f"擷取 EBS 磁碟失敗: {e}")
            return []
    
    def _extract_rds_instances(self) -> List[Dict[str, Any]]:
        """擷取 RDS 實例"""
        logger.info("擷取 RDS 實例...")
        rds = self.session.client('rds', region_name=self.region)
        
        try:
            response = rds.describe_db_instances()
            instances = []
            
            for db in response['DBInstances']:
                db_data = {
                    'DBInstanceIdentifier': db['DBInstanceIdentifier'],
                    'DBInstanceClass': db['DBInstanceClass'],
                    'Engine': db['Engine'],
                    'EngineVersion': db['EngineVersion'],
                    'DBInstanceStatus': db['DBInstanceStatus'],
                    'MasterUsername': db['MasterUsername'],
                    'DBName': db.get('DBName'),
                    'VpcId': db.get('DBSubnetGroup', {}).get('VpcId'),
                    'Region': self.region,
                    'CreatedTime': db['InstanceCreateTime'].isoformat()
                }
                instances.append(db_data)
            
            logger.info(f"擷取到 {len(instances)} 個 RDS 實例")
            return instances
            
        except ClientError as e:
            logger.error(f"擷取 RDS 實例失敗: {e}")
            return []
    
    def _extract_lambda_functions(self) -> List[Dict[str, Any]]:
        """擷取 Lambda 函數"""
        logger.info("擷取 Lambda 函數...")
        lambda_client = self.session.client('lambda', region_name=self.region)
        
        try:
            response = lambda_client.list_functions()
            functions = []
            
            for func in response['Functions']:
                func_data = {
                    'FunctionName': func['FunctionName'],
                    'Runtime': func['Runtime'],
                    'Handler': func['Handler'],
                    'CodeSize': func['CodeSize'],
                    'Description': func.get('Description', ''),
                    'Timeout': func['Timeout'],
                    'MemorySize': func['MemorySize'],
                    'LastModified': func['LastModified'],
                    'Region': self.region
                }
                functions.append(func_data)
            
            logger.info(f"擷取到 {len(functions)} 個 Lambda 函數")
            return functions
            
        except ClientError as e:
            logger.error(f"擷取 Lambda 函數失敗: {e}")
            return []
    
    def _get_tag_value(self, tags: List[Dict[str, str]], key: str, default: str = "") -> str:
        """從標籤列表中獲取指定鍵的值"""
        for tag in tags:
            if tag.get('Key') == key:
                return tag.get('Value', default)
        return default
    
    def save_to_file(self, output_path: str) -> None:
        """將擷取的資料儲存到檔案"""
        try:
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(self.resources, f, indent=2, ensure_ascii=False)
            
            logger.info(f"資料已儲存到: {output_path}")
            
        except Exception as e:
            logger.error(f"儲存資料失敗: {e}")
            raise


# 使用範例
if __name__ == "__main__":
    # 設定日誌
    logger.add("aws_extraction.log", rotation="1 day", retention="7 days")
    
    try:
        # 創建擷取器
        extractor = AWSExtractor(region="us-east-1")
        
        # 擷取所有資源
        resources = extractor.extract_all_resources()
        
        # 儲存到檔案
        output_path = "data/raw/aws_resources.json"
        extractor.save_to_file(output_path)
        
        print("AWS 資源擷取完成！")
        print(f"擷取的資源類型: {list(resources.keys())}")
        
    except Exception as e:
        logger.error(f"擷取失敗: {e}")
        print(f"擷取失敗: {e}")
