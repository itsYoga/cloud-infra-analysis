#!/usr/bin/env python3
"""
增強版模擬 AWS 資料生成器

基於 Cartography 分析，生成更真實、更豐富的模擬資料，
包含完整的資源關聯性和安全規則。
"""

import json
import random
import secrets
from datetime import datetime, timedelta
from typing import List, Dict, Any


def _generate_aws_id(prefix: str, length: int = 17) -> str:
    """產生一個 AWS 格式的十六進位 ID"""
    return f"{prefix}-{secrets.token_hex(length // 2 + 1)[:length]}"


def _generate_arn(partition: str, service: str, region: str, account_id: str, resource_path: str) -> str:
    """產生一個標準的 AWS ARN"""
    return f"arn:{partition}:{service}:{region}:{account_id}:{resource_path}"


class EnhancedMockAWSDataGenerator:
    """增強版模擬 AWS 資料生成器"""
    
    def __init__(self):
        self.regions = ['us-east-1', 'us-west-2', 'eu-west-1', 'ap-southeast-1', 'ap-northeast-1']
        self.instance_types = ['t2.micro', 't2.small', 't2.medium', 't3.micro', 't3.small', 't3.medium', 'm5.large', 'c5.xlarge', 'r5.large']
        self.volume_types = ['gp2', 'gp3', 'io1', 'io2', 'st1', 'sc1']
        self.states = ['running', 'stopped', 'pending', 'terminated']
        
        # AWS 帳戶和分區資訊
        self.account_id = '123456789012'
        self.partition = 'aws'
        self.id_gen = _generate_aws_id
        
        # 真實的應用程式架構
        self.app_architectures = {
            'web-tier': ['web-server', 'load-balancer', 'api-gateway'],
            'app-tier': ['api-server', 'microservice', 'auth-service', 'payment-processor'],
            'data-tier': ['database', 'cache-server', 'search-engine', 'analytics'],
            'infrastructure': ['monitoring', 'logging', 'backup', 'security']
        }
        
        # 真實的安全群組名稱
        self.security_group_names = [
            'web-servers', 'api-servers', 'database-servers', 'cache-servers',
            'load-balancers', 'monitoring', 'bastion-hosts', 'nat-gateways',
            'vpc-endpoints', 'lambda-functions', 'rds-proxy', 'elasticsearch'
        ]
        
        # 常見的端口和協議
        self.common_ports = {
            'web-servers': [80, 443, 8080],
            'api-servers': [3000, 8000, 9000],
            'database-servers': [3306, 5432, 6379, 27017],
            'monitoring': [9100, 9090, 3000],
            'ssh': [22],
            'rdp': [3389],
            'dns': [53]
        }
    
    def generate_vpcs(self, count: int = 5) -> List[Dict[str, Any]]:
        """生成 VPC"""
        vpcs = []
        vpc_names = ['production-vpc', 'staging-vpc', 'development-vpc', 'dmz-vpc', 'management-vpc']
        
        for i in range(count):
            region = random.choice(self.regions)
            vpc_id = self.id_gen('vpc')
            name = vpc_names[i] if i < len(vpc_names) else f'vpc-{i+1:02d}'
            
            vpc = {
                'VpcId': vpc_id,
                'Name': name,
                'CidrBlock': f'10.{i}.0.0/16',
                'State': 'available',
                'IsDefault': i == 0,
                'Region': region,
                'Arn': _generate_arn(self.partition, 'ec2', region, self.account_id, f"vpc/{vpc_id}"),
                'Tags': [
                    {'Key': 'Name', 'Value': name},
                    {'Key': 'Environment', 'Value': 'prod' if 'production' in name else 'dev'},
                    {'Key': 'Purpose', 'Value': 'application' if 'prod' in name else 'testing'}
                ]
            }
            vpcs.append(vpc)
        
        return vpcs
    
    def generate_subnets(self, vpcs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """生成子網路"""
        subnets = []
        subnet_types = ['public', 'private', 'database', 'cache']
        
        for vpc in vpcs:
            vpc_id = vpc['VpcId']
            region = vpc['Region']
            base_cidr = vpc['CidrBlock'].split('.')[1]
            
            # 每個 VPC 生成 4-6 個子網路
            subnet_count = random.randint(4, 6)
            for i in range(subnet_count):
                subnet_type = random.choice(subnet_types)
                az_suffix = chr(ord('a') + (i % 3))  # a, b, c
                availability_zone = f"{region}{az_suffix}"
                
                subnet = {
                    'SubnetId': self.id_gen('subnet'),
                    'Name': f'{vpc["Name"]}-{subnet_type}-{i+1:02d}',
                    'CidrBlock': f'10.{base_cidr}.{i*16}.0/24',
                    'AvailabilityZone': availability_zone,
                    'VpcId': vpc_id,
                    'State': 'available',
                    'Region': region,
                    'Arn': _generate_arn(self.partition, 'ec2', region, self.account_id, f"subnet/{self.id_gen('subnet')}"),
                    'Tags': [
                        {'Key': 'Name', 'Value': f'{vpc["Name"]}-{subnet_type}-{i+1:02d}'},
                        {'Key': 'Type', 'Value': subnet_type},
                        {'Key': 'VPC', 'Value': vpc_id}
                    ]
                }
                subnets.append(subnet)
        
        return subnets
    
    def generate_security_groups(self, count: int = 15, vpcs: List[Dict[str, Any]] = []) -> List[Dict[str, Any]]:
        """生成安全群組"""
        security_groups = []
        
        for i in range(count):
            vpc = random.choice(vpcs) if vpcs else {'VpcId': self.id_gen('vpc'), 'Region': random.choice(self.regions)}
            vpc_id = vpc['VpcId']
            region = vpc['Region']
            
            group_name = random.choice(self.security_group_names)
            group_id = self.id_gen('sg')
            
            sg = {
                'GroupID': group_id,
                'GroupName': f'{group_name}-{random.choice(["prod", "staging", "dev"])}',
                'Description': f'Security group for {group_name}',
                'VpcId': vpc_id,
                'Region': region,
                'Arn': _generate_arn(self.partition, 'ec2', region, self.account_id, f"security-group/{group_id}"),
                'Tags': [
                    {'Key': 'Name', 'Value': f'{group_name}-{random.choice(["prod", "staging", "dev"])}'},
                    {'Key': 'Purpose', 'Value': group_name},
                    {'Key': 'VPC', 'Value': vpc_id}
                ]
            }
            security_groups.append(sg)
        
        return security_groups
    
    def generate_security_rules(self, security_groups: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """生成安全規則"""
        rules = []
        
        for sg in security_groups:
            group_id = sg['GroupID']
            group_name = sg['GroupName']
            
            # 為每個安全群組生成 2-5 個規則
            rule_count = random.randint(2, 5)
            
            for i in range(rule_count):
                # 根據安全群組類型生成相應的規則
                if 'web' in group_name.lower():
                    ports = random.choice(self.common_ports['web-servers'])
                    protocol = 'tcp'
                    source = '0.0.0.0/0' if random.random() > 0.3 else '10.0.0.0/8'
                elif 'api' in group_name.lower():
                    ports = random.choice(self.common_ports['api-servers'])
                    protocol = 'tcp'
                    source = '10.0.0.0/8' if random.random() > 0.2 else '0.0.0.0/0'
                elif 'database' in group_name.lower():
                    ports = random.choice(self.common_ports['database-servers'])
                    protocol = 'tcp'
                    source = '10.0.0.0/8'  # 資料庫通常只允許內網訪問
                elif 'monitoring' in group_name.lower():
                    ports = random.choice(self.common_ports['monitoring'])
                    protocol = 'tcp'
                    source = '10.0.0.0/8'
                else:
                    ports = random.randint(1, 65535)
                    protocol = random.choice(['tcp', 'udp', 'icmp'])
                    source = random.choice(['0.0.0.0/0', '10.0.0.0/8', '172.16.0.0/12'])
                
                direction = random.choice(['inbound', 'outbound'])
                action = 'allow' if random.random() > 0.1 else 'deny'
                
                rule = {
                    'RuleId': f'{group_id}-rule-{i+1}',
                    'GroupId': group_id,
                    'Protocol': protocol,
                    'PortRange': f'{ports}-{ports}' if protocol != 'icmp' else '0-65535',
                    'SourceCIDR': source,
                    'Direction': direction,
                    'Action': action,
                    'Description': f'Rule for {group_name} {direction} traffic'
                }
                rules.append(rule)
        
        return rules
    
    def generate_ec2_instances(self, count: int = 30, 
                             vpcs: List[Dict[str, Any]] = [], 
                             subnets: List[Dict[str, Any]] = [], 
                             security_groups: List[Dict[str, Any]] = []) -> List[Dict[str, Any]]:
        """生成 EC2 實例"""
        instances = []
        
        # 真實的應用程式名稱
        app_names = [
            'web-server', 'api-gateway', 'database-proxy', 'load-balancer', 'cache-server',
            'monitoring', 'logging', 'analytics', 'auth-service', 'payment-processor',
            'user-service', 'notification-service', 'file-storage', 'search-engine',
            'recommendation-engine', 'order-service', 'inventory-service', 'shipping-service',
            'customer-service', 'admin-panel', 'reporting-service', 'audit-service',
            'backup-service', 'disaster-recovery', 'testing-service'
        ]
        
        environments = ['prod', 'staging', 'dev', 'test', 'demo']
        teams = ['backend', 'frontend', 'data', 'infrastructure', 'security', 'mobile', 'devops']
        
        for i in range(count):
            app_name = random.choice(app_names)
            env = random.choice(environments)
            team = random.choice(teams)
            
            # 隨機選一個已存在的 VPC
            chosen_vpc = random.choice(vpcs) if vpcs else {'VpcId': self.id_gen('vpc'), 'Region': random.choice(self.regions)}
            region = chosen_vpc['Region']
            
            # 從該 VPC 的子網路中隨機選一個
            subnets_in_vpc = [s for s in subnets if s['VpcId'] == chosen_vpc['VpcId']]
            chosen_subnet = random.choice(subnets_in_vpc) if subnets_in_vpc else {'SubnetId': self.id_gen('subnet'), 'AvailabilityZone': f'{region}a'}
            
            # 從該 VPC 的安全群組中隨機選 1-3 個
            sgs_in_vpc = [sg for sg in security_groups if sg['VpcId'] == chosen_vpc['VpcId']]
            chosen_sgs = random.sample(sgs_in_vpc, k=random.randint(1, min(3, len(sgs_in_vpc)))) if sgs_in_vpc else [{'GroupID': self.id_gen('sg'), 'GroupName': 'default-sg'}]
            
            # 將 SG 格式化為 EC2 期待的格式
            sg_list_for_ec2 = [{'GroupId': sg['GroupID'], 'GroupName': sg['GroupName']} for sg in chosen_sgs]
            
            instance_state = random.choice(self.states)
            instance_id = self.id_gen('i')
            
            # 根據應用程式類型選擇實例類型
            if 'database' in app_name or 'cache' in app_name:
                instance_type = random.choice(['r5.large', 'm5.large', 'c5.xlarge'])
            elif 'web' in app_name or 'api' in app_name:
                instance_type = random.choice(['t3.medium', 't3.small', 'm5.large'])
            else:
                instance_type = random.choice(self.instance_types)
            
            instance = {
                'InstanceID': instance_id,
                'ImageId': self.id_gen('ami'),
                'Name': f'{app_name}-{env}-{i+1:02d}',
                'State': {'Name': instance_state},
                'InstanceType': instance_type,
                'PublicIpAddress': f'54.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(0,255)}' if instance_state == 'running' and random.random() > 0.3 else None,
                'PrivateIpAddress': f'10.{random.randint(0,255)}.{random.randint(0,255)}.{random.randint(0,255)}',
                'LaunchTime': (datetime.now() - timedelta(days=random.randint(1, 365))).isoformat(),
                'Placement': {'AvailabilityZone': chosen_subnet['AvailabilityZone']},
                'SecurityGroups': sg_list_for_ec2,
                'SubnetId': chosen_subnet['SubnetId'],
                'VpcId': chosen_vpc['VpcId'],
                'Arn': _generate_arn(self.partition, 'ec2', region, self.account_id, f"instance/{instance_id}"),
                'Tags': [
                    {'Key': 'Name', 'Value': f'{app_name}-{env}-{i+1:02d}'},
                    {'Key': 'Environment', 'Value': env},
                    {'Key': 'Team', 'Value': team},
                    {'Key': 'Application', 'Value': app_name},
                    {'Key': 'Owner', 'Value': f'{team}-team@company.com'},
                    {'Key': 'CostCenter', 'Value': f'CC-{random.randint(1000, 9999)}'},
                    {'Key': 'Backup', 'Value': 'daily' if env == 'prod' else 'weekly'},
                    {'Key': 'Monitoring', 'Value': 'enabled'}
                ]
            }
            instances.append(instance)
        
        return instances
    
    def generate_ebs_volumes(self, count: int = 25, ec2_instances: List[Dict[str, Any]] = []) -> List[Dict[str, Any]]:
        """生成 EBS 磁碟"""
        volumes = []
        
        # 篩選出可附加的實例
        attachable_instances = [inst for inst in ec2_instances if inst['State']['Name'] != 'terminated']
        
        for i in range(count):
            volume_state = random.choice(['available', 'in-use', 'creating', 'deleting'])
            volume_id = self.id_gen('vol')
            volume_type = random.choice(self.volume_types)
            size = random.randint(8, 1000)  # 8GB 到 1TB
            
            volume = {
                'VolumeId': volume_id,
                'Size': size,
                'VolumeType': volume_type,
                'State': volume_state,
                'Encrypted': random.random() > 0.2,  # 80% 加密
                'KmsKeyId': f'arn:aws:kms:us-east-1:{self.account_id}:key/{self.id_gen("key")}' if random.random() > 0.3 else None,
                'Region': random.choice(self.regions),
                'Arn': _generate_arn(self.partition, 'ec2', 'us-east-1', self.account_id, f"volume/{volume_id}"),
                'Tags': [
                    {'Key': 'Name', 'Value': f'volume-{i+1:03d}'},
                    {'Key': 'Type', 'Value': volume_type},
                    {'Key': 'Backup', 'Value': 'enabled' if size > 100 else 'disabled'}
                ]
            }
            
            # 如果是 in-use 狀態，附加到實例
            if volume_state == 'in-use' and attachable_instances:
                chosen_instance = random.choice(attachable_instances)
                volume['Region'] = chosen_instance['Placement']['AvailabilityZone'][:-1]  # 移除 AZ 後綴
                volume['Attachments'] = [{
                    'InstanceId': chosen_instance['InstanceID'],
                    'Device': '/dev/sdf',
                    'State': 'attached',
                    'AttachTime': (datetime.now() - timedelta(days=random.randint(1, 50))).isoformat()
                }]
            
            volumes.append(volume)
        
        return volumes
    
    def generate_rds_instances(self, count: int = 8, vpcs: List[Dict[str, Any]] = [], subnets: List[Dict[str, Any]] = []) -> List[Dict[str, Any]]:
        """生成 RDS 實例"""
        rds_instances = []
        db_engines = ['mysql', 'postgres', 'oracle', 'sqlserver', 'mariadb']
        
        for i in range(count):
            vpc = random.choice(vpcs) if vpcs else {'VpcId': self.id_gen('vpc'), 'Region': random.choice(self.regions)}
            region = vpc['Region']
            
            db_identifier = f'db-{random.choice(["prod", "staging", "dev"])}-{i+1:02d}'
            engine = random.choice(db_engines)
            
            rds = {
                'DBInstanceIdentifier': db_identifier,
                'DBInstanceClass': random.choice(['db.t3.micro', 'db.t3.small', 'db.r5.large', 'db.m5.xlarge']),
                'Engine': engine,
                'EngineVersion': f'{random.randint(5, 8)}.{random.randint(0, 9)}.{random.randint(0, 9)}',
                'DBInstanceStatus': random.choice(['available', 'backing-up', 'modifying']),
                'MasterUsername': f'admin{random.randint(100, 999)}',
                'AllocatedStorage': random.randint(20, 1000),
                'StorageType': random.choice(['gp2', 'gp3', 'io1']),
                'VpcId': vpc['VpcId'],
                'Region': region,
                'Arn': _generate_arn(self.partition, 'rds', region, self.account_id, f"db:{db_identifier}"),
                'Tags': [
                    {'Key': 'Name', 'Value': db_identifier},
                    {'Key': 'Environment', 'Value': 'prod' if 'prod' in db_identifier else 'dev'},
                    {'Key': 'Backup', 'Value': 'enabled'},
                    {'Key': 'Monitoring', 'Value': 'enabled'}
                ]
            }
            rds_instances.append(rds)
        
        return rds_instances
    
    def generate_load_balancers(self, count: int = 8, vpcs: List[Dict[str, Any]] = []) -> List[Dict[str, Any]]:
        """生成負載平衡器"""
        load_balancers = []
        
        for i in range(count):
            vpc = random.choice(vpcs) if vpcs else {'VpcId': self.id_gen('vpc'), 'Region': random.choice(self.regions)}
            region = vpc['Region']
            
            lb_name = f'lb-{random.choice(["web", "api", "internal"])}-{i+1:02d}'
            lb_id = self.id_gen('lb')
            
            lb = {
                'LoadBalancerId': lb_id,
                'LoadBalancerName': lb_name,
                'DNSName': f'{lb_id}.{region}.elb.amazonaws.com',
                'State': random.choice(['active', 'provisioning']),
                'Type': random.choice(['application', 'network', 'gateway']),
                'Scheme': random.choice(['internet-facing', 'internal']),
                'VpcId': vpc['VpcId'],
                'Region': region,
                'Arn': _generate_arn(self.partition, 'elasticloadbalancing', region, self.account_id, f"loadbalancer/{lb_id}"),
                'Tags': [
                    {'Key': 'Name', 'Value': lb_name},
                    {'Key': 'Type', 'Value': 'load-balancer'},
                    {'Key': 'Environment', 'Value': random.choice(['prod', 'staging', 'dev'])}
                ]
            }
            load_balancers.append(lb)
        
        return load_balancers
    
    def generate_s3_buckets(self, count: int = 12) -> List[Dict[str, Any]]:
        """生成 S3 儲存桶"""
        buckets = []
        bucket_purposes = ['logs', 'backups', 'static-assets', 'data-lake', 'documents', 'images', 'videos', 'archives']
        
        for i in range(count):
            purpose = random.choice(bucket_purposes)
            bucket_name = f'company-{purpose}-{random.randint(1000, 9999)}'
            region = random.choice(self.regions)
            
            bucket = {
                'BucketName': bucket_name,
                'CreationDate': (datetime.now() - timedelta(days=random.randint(1, 1000))).isoformat(),
                'Region': region,
                'Arn': _generate_arn(self.partition, 's3', '', '', bucket_name),
                'Tags': [
                    {'Key': 'Name', 'Value': bucket_name},
                    {'Key': 'Purpose', 'Value': purpose},
                    {'Key': 'Environment', 'Value': random.choice(['prod', 'staging', 'dev'])},
                    {'Key': 'Retention', 'Value': '7-years' if purpose == 'archives' else '1-year'}
                ]
            }
            buckets.append(bucket)
        
        return buckets
    
    def generate_lambda_functions(self, count: int = 10) -> List[Dict[str, Any]]:
        """生成 Lambda 函數"""
        functions = []
        function_names = ['data-processor', 'image-resizer', 'email-sender', 'notification-handler', 
                         'api-handler', 'scheduled-task', 'event-processor', 'webhook-handler']
        
        for i in range(count):
            func_name = random.choice(function_names)
            function_name = f'{func_name}-{random.choice(["prod", "staging", "dev"])}-{i+1:02d}'
            region = random.choice(self.regions)
            
            function = {
                'FunctionName': function_name,
                'FunctionArn': _generate_arn(self.partition, 'lambda', region, self.account_id, f"function:{function_name}"),
                'Runtime': random.choice(['python3.9', 'python3.8', 'nodejs18.x', 'java11', 'go1.x']),
                'Handler': 'index.handler',
                'CodeSize': random.randint(1000, 50000000),
                'Description': f'Lambda function for {func_name}',
                'Timeout': random.randint(3, 900),
                'MemorySize': random.choice([128, 256, 512, 1024, 2048]),
                'LastModified': (datetime.now() - timedelta(days=random.randint(1, 30))).isoformat(),
                'Region': region,
                'Tags': [
                    {'Key': 'Name', 'Value': function_name},
                    {'Key': 'Purpose', 'Value': func_name},
                    {'Key': 'Environment', 'Value': random.choice(['prod', 'staging', 'dev'])}
                ]
            }
            functions.append(function)
        
        return functions
    
    def generate_complete_dataset(self) -> Dict[str, Any]:
        """生成完整的模擬資料集"""
        print("生成增強版模擬 AWS 資料...")
        
        # 按順序生成資源以確保關聯性
        vpcs = self.generate_vpcs(5)
        subnets = self.generate_subnets(vpcs)
        security_groups = self.generate_security_groups(15, vpcs)
        security_rules = self.generate_security_rules(security_groups)
        ec2_instances = self.generate_ec2_instances(30, vpcs, subnets, security_groups)
        ebs_volumes = self.generate_ebs_volumes(25, ec2_instances)
        rds_instances = self.generate_rds_instances(8, vpcs, subnets)
        load_balancers = self.generate_load_balancers(8, vpcs)
        s3_buckets = self.generate_s3_buckets(12)
        lambda_functions = self.generate_lambda_functions(10)
        
        # 組合完整資料集
        dataset = {
            'metadata': {
                'extraction_time': datetime.now().isoformat(),
                'account_id': self.account_id,
                'data_type': 'enhanced_mock_data',
                'version': '2.0',
                'description': 'Enhanced mock AWS data with realistic relationships and security rules'
            },
            'ec2_instances': {
                'Reservations': [{
                    'ReservationId': self.id_gen('r'),
                    'OwnerId': self.account_id,
                    'Groups': [],
                    'Instances': ec2_instances
                }]
            },
            'security_groups': {'SecurityGroups': security_groups},
            'security_rules': {'Rules': security_rules},
            'vpcs': {'Vpcs': vpcs},
            'subnets': {'Subnets': subnets},
            'load_balancers': {'LoadBalancers': load_balancers},
            's3_buckets': {'Buckets': s3_buckets, 'Owner': {'DisplayName': 'mock-owner', 'ID': 'mock-owner-id'}},
            'ebs_volumes': {'Volumes': ebs_volumes},
            'rds_instances': {'DBInstances': rds_instances},
            'lambda_functions': {'Functions': lambda_functions}
        }
        
        print(f"生成完成:")
        print(f"- EC2 實例: {len(ec2_instances)}")
        print(f"- 安全群組: {len(security_groups)}")
        print(f"- 安全規則: {len(security_rules)}")
        print(f"- VPC: {len(vpcs)}")
        print(f"- 子網路: {len(subnets)}")
        print(f"- EBS 磁碟: {len(ebs_volumes)}")
        print(f"- RDS 實例: {len(rds_instances)}")
        print(f"- 負載平衡器: {len(load_balancers)}")
        print(f"- S3 儲存桶: {len(s3_buckets)}")
        print(f"- Lambda 函數: {len(lambda_functions)}")
        
        return dataset


def main():
    """主函數"""
    generator = EnhancedMockAWSDataGenerator()
    dataset = generator.generate_complete_dataset()
    
    # 儲存到檔案
    output_file = 'data/raw/enhanced_mock_aws_resources.json'
    import os
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(dataset, f, indent=2, ensure_ascii=False)
    
    print(f"\n增強版模擬資料已儲存至: {output_file}")


if __name__ == '__main__':
    main()
