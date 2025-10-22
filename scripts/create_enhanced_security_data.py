#!/usr/bin/env python3
"""
增強版安全測試資料生成器

生成包含多種安全問題的測試資料，修正資料載入問題。
"""

import json
import random
import secrets
from datetime import datetime, timedelta
from typing import List, Dict, Any


def _generate_aws_id(prefix: str, length: int = 17) -> str:
    """產生一個 AWS 格式的十六進位 ID"""
    return f"{prefix}-{secrets.token_hex(length // 2 + 1)[:length]}"


class EnhancedSecurityDataGenerator:
    """增強版安全測試資料生成器"""
    
    def __init__(self):
        self.regions = ['us-east-1', 'us-west-2', 'eu-west-1']
        self.instance_types = ['t2.micro', 't2.small', 't3.medium', 'm5.large']
        self.states = ['running', 'stopped', 'pending']
        
        # 真實的應用程式架構
        self.app_services = [
            'web-server', 'api-server', 'database-server', 'cache-server',
            'auth-service', 'payment-service', 'notification-service',
            'analytics-service', 'monitoring-service', 'backup-service'
        ]
        
        # 環境
        self.environments = ['prod', 'staging', 'dev', 'test']
        
    def generate_complete_dataset(self) -> Dict[str, Any]:
        """生成完整的測試資料集"""
        print("生成增強版安全測試資料...")
        
        # 生成基礎設施
        vpcs = self._generate_vpcs(4)
        subnets = self._generate_subnets(vpcs, 4)
        security_groups = self._generate_security_groups(vpcs)
        instances = self._generate_ec2_instances(subnets, security_groups)
        volumes = self._generate_ebs_volumes(instances)
        security_rules = self._generate_security_rules(security_groups)
        
        # 按照系統期望的格式組織資料
        dataset = {
            'metadata': {
                'extraction_time': datetime.now().isoformat(),
                'account_id': '123456789012',
                'data_type': 'enhanced_security_test_data',
                'version': '2.0',
                'description': 'Enhanced security test data with multiple vulnerabilities'
            },
            'vpcs': {'Vpcs': vpcs},
            'subnets': {'Subnets': subnets},
            'security_groups': {'SecurityGroups': security_groups},
            'security_rules': {'Rules': security_rules},
            'ec2_instances': {'Reservations': [{'Instances': instances}]},
            'ebs_volumes': {'Volumes': volumes}
        }
        
        print(f"生成完成：{len(vpcs)} VPCs, {len(subnets)} Subnets, {len(security_groups)} Security Groups, {len(instances)} Instances, {len(volumes)} Volumes, {len(security_rules)} Security Rules")
        return dataset
    
    def _generate_vpcs(self, count: int = 4) -> List[Dict]:
        """生成 VPC"""
        vpcs = []
        for i in range(count):
            vpc_id = _generate_aws_id('vpc')
            vpc = {
                'VpcId': vpc_id,
                'CidrBlock': f'10.{i}.0.0/16',
                'State': 'available',
                'IsDefault': i == 0,
                'Tags': [
                    {'Key': 'Name', 'Value': f'vpc-{self.environments[i % len(self.environments)]}-{i+1}'},
                    {'Key': 'Environment', 'Value': self.environments[i % len(self.environments)]}
                ]
            }
            vpcs.append(vpc)
        return vpcs
    
    def _generate_subnets(self, vpcs: List[Dict], count_per_vpc: int = 4) -> List[Dict]:
        """生成子網路"""
        subnets = []
        for vpc in vpcs:
            for i in range(count_per_vpc):
                subnet_id = _generate_aws_id('subnet')
                subnet = {
                    'SubnetId': subnet_id,
                    'VpcId': vpc['VpcId'],
                    'CidrBlock': f'10.{vpcs.index(vpc)}.{i}.0/24',
                    'AvailabilityZone': f'{self.regions[0]}{chr(97+i)}',
                    'State': 'available',
                    'Tags': [
                        {'Key': 'Name', 'Value': f'subnet-{vpc["Tags"][0]["Value"]}-{i+1}'},
                        {'Key': 'Environment', 'Value': vpc['Tags'][1]['Value']}
                    ]
                }
                subnets.append(subnet)
        return subnets
    
    def _generate_security_groups(self, vpcs: List[Dict]) -> List[Dict]:
        """生成安全群組，包含多種安全問題"""
        security_groups = []
        
        for vpc in vpcs:
            # 正常的安全群組
            normal_sg = {
                'GroupId': _generate_aws_id('sg'),
                'GroupName': f'normal-{vpc["Tags"][0]["Value"]}',
                'Description': 'Normal security group',
                'VpcId': vpc['VpcId'],
                'IpPermissions': [
                    {
                        'IpProtocol': 'tcp',
                        'FromPort': 80,
                        'ToPort': 80,
                        'IpRanges': [{'CidrIp': '0.0.0.0/0'}]
                    }
                ]
            }
            security_groups.append(normal_sg)
            
            # 過度寬鬆的安全群組 (問題1)
            overly_permissive_sg = {
                'GroupId': _generate_aws_id('sg'),
                'GroupName': f'overly-permissive-{vpc["Tags"][0]["Value"]}',
                'Description': 'Overly permissive security group',
                'VpcId': vpc['VpcId'],
                'IpPermissions': [
                    {
                        'IpProtocol': 'tcp',
                        'FromPort': 0,
                        'ToPort': 65535,
                        'IpRanges': [{'CidrIp': '0.0.0.0/0'}]
                    }
                ]
            }
            security_groups.append(overly_permissive_sg)
            
            # 暴露 SSH 的安全群組 (問題2)
            exposed_ssh_sg = {
                'GroupId': _generate_aws_id('sg'),
                'GroupName': f'exposed-ssh-{vpc["Tags"][0]["Value"]}',
                'Description': 'Security group with exposed SSH',
                'VpcId': vpc['VpcId'],
                'IpPermissions': [
                    {
                        'IpProtocol': 'tcp',
                        'FromPort': 22,
                        'ToPort': 22,
                        'IpRanges': [{'CidrIp': '0.0.0.0/0'}]
                    }
                ]
            }
            security_groups.append(exposed_ssh_sg)
            
            # 暴露 RDP 的安全群組 (問題3)
            exposed_rdp_sg = {
                'GroupId': _generate_aws_id('sg'),
                'GroupName': f'exposed-rdp-{vpc["Tags"][0]["Value"]}',
                'Description': 'Security group with exposed RDP',
                'VpcId': vpc['VpcId'],
                'IpPermissions': [
                    {
                        'IpProtocol': 'tcp',
                        'FromPort': 3389,
                        'ToPort': 3389,
                        'IpRanges': [{'CidrIp': '0.0.0.0/0'}]
                    }
                ]
            }
            security_groups.append(exposed_rdp_sg)
            
            # 未使用的安全群組 (問題4)
            unused_sg = {
                'GroupId': _generate_aws_id('sg'),
                'GroupName': f'unused-{vpc["Tags"][0]["Value"]}',
                'Description': 'Unused security group',
                'VpcId': vpc['VpcId'],
                'IpPermissions': []
            }
            security_groups.append(unused_sg)
            
            # 額外的未使用安全群組 (問題5)
            unused_sg2 = {
                'GroupId': _generate_aws_id('sg'),
                'GroupName': f'unused-2-{vpc["Tags"][0]["Value"]}',
                'Description': 'Another unused security group',
                'VpcId': vpc['VpcId'],
                'IpPermissions': []
            }
            security_groups.append(unused_sg2)
        
        return security_groups
    
    def _generate_ec2_instances(self, subnets: List[Dict], security_groups: List[Dict]) -> List[Dict]:
        """生成 EC2 實例，包含多種安全問題"""
        instances = []
        
        for i, subnet in enumerate(subnets):
            # 正常實例
            if i % 3 == 0:
                instance = {
                    'InstanceId': _generate_aws_id('i'),
                    'InstanceType': random.choice(self.instance_types),
                    'State': {'Name': 'running'},
                    'PublicIpAddress': f'54.{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}',
                    'PrivateIpAddress': f'10.{subnet["CidrBlock"].split(".")[1]}.{subnet["CidrBlock"].split(".")[2]}.{random.randint(10,250)}',
                    'SubnetId': subnet['SubnetId'],
                    'VpcId': subnet['VpcId'],
                    'SecurityGroups': [random.choice([sg for sg in security_groups if sg['VpcId'] == subnet['VpcId'] and 'normal' in sg['GroupName']])],
                    'Tags': [
                        {'Key': 'Name', 'Value': f'{random.choice(self.app_services)}-{i+1}'},
                        {'Key': 'Environment', 'Value': subnet['Tags'][1]['Value']}
                    ]
                }
                instances.append(instance)
            
            # 暴露 SSH 的實例
            if i % 4 == 0:
                exposed_ssh_instance = {
                    'InstanceId': _generate_aws_id('i'),
                    'InstanceType': random.choice(self.instance_types),
                    'State': {'Name': 'running'},
                    'PublicIpAddress': f'54.{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}',
                    'PrivateIpAddress': f'10.{subnet["CidrBlock"].split(".")[1]}.{subnet["CidrBlock"].split(".")[2]}.{random.randint(10,250)}',
                    'SubnetId': subnet['SubnetId'],
                    'VpcId': subnet['VpcId'],
                    'SecurityGroups': [sg for sg in security_groups if 'exposed-ssh' in sg['GroupName'] and sg['VpcId'] == subnet['VpcId']],
                    'Tags': [
                        {'Key': 'Name', 'Value': f'ssh-exposed-server-{i+1}'},
                        {'Key': 'Environment', 'Value': subnet['Tags'][1]['Value']}
                    ]
                }
                instances.append(exposed_ssh_instance)
            
            # 暴露 RDP 的實例
            if i % 5 == 0:
                exposed_rdp_instance = {
                    'InstanceId': _generate_aws_id('i'),
                    'InstanceType': random.choice(self.instance_types),
                    'State': {'Name': 'running'},
                    'PublicIpAddress': f'54.{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}',
                    'PrivateIpAddress': f'10.{subnet["CidrBlock"].split(".")[1]}.{subnet["CidrBlock"].split(".")[2]}.{random.randint(10,250)}',
                    'SubnetId': subnet['SubnetId'],
                    'VpcId': subnet['VpcId'],
                    'SecurityGroups': [sg for sg in security_groups if 'exposed-rdp' in sg['GroupName'] and sg['VpcId'] == subnet['VpcId']],
                    'Tags': [
                        {'Key': 'Name', 'Value': f'rdp-exposed-server-{i+1}'},
                        {'Key': 'Environment', 'Value': subnet['Tags'][1]['Value']}
                    ]
                }
                instances.append(exposed_rdp_instance)
            
            # 過度寬鬆安全群組的實例
            if i % 6 == 0:
                overly_permissive_instance = {
                    'InstanceId': _generate_aws_id('i'),
                    'InstanceType': random.choice(self.instance_types),
                    'State': {'Name': 'running'},
                    'PublicIpAddress': f'54.{random.randint(1,255)}.{random.randint(1,255)}.{random.randint(1,255)}',
                    'PrivateIpAddress': f'10.{subnet["CidrBlock"].split(".")[1]}.{subnet["CidrBlock"].split(".")[2]}.{random.randint(10,250)}',
                    'SubnetId': subnet['SubnetId'],
                    'VpcId': subnet['VpcId'],
                    'SecurityGroups': [sg for sg in security_groups if 'overly-permissive' in sg['GroupName'] and sg['VpcId'] == subnet['VpcId']],
                    'Tags': [
                        {'Key': 'Name', 'Value': f'overly-permissive-server-{i+1}'},
                        {'Key': 'Environment', 'Value': subnet['Tags'][1]['Value']}
                    ]
                }
                instances.append(overly_permissive_instance)
        
        return instances
    
    def _generate_ebs_volumes(self, instances: List[Dict]) -> List[Dict]:
        """生成 EBS 磁碟，包含多種安全問題"""
        volumes = []
        
        for instance in instances:
            # 正常加密的磁碟
            encrypted_volume = {
                'VolumeId': _generate_aws_id('vol'),
                'Size': random.randint(20, 100),
                'VolumeType': random.choice(['gp2', 'gp3']),
                'State': 'in-use',
                'Encrypted': True,
                'Iops': random.randint(100, 3000),
                'CreationDate': (datetime.now() - timedelta(days=random.randint(1, 365))).isoformat(),
                'Attachments': [{'InstanceId': instance['InstanceId']}],
                'Tags': [
                    {'Key': 'Name', 'Value': f'encrypted-volume-{instance["InstanceId"]}'}
                ]
            }
            volumes.append(encrypted_volume)
            
            # 未加密的磁碟 (問題6)
            if random.random() < 0.4:  # 40% 機率
                unencrypted_volume = {
                    'VolumeId': _generate_aws_id('vol'),
                    'Size': random.randint(20, 100),
                    'VolumeType': random.choice(['gp2', 'gp3']),
                    'State': 'in-use',
                    'Encrypted': False,  # 問題：未加密
                    'Iops': random.randint(100, 3000),
                    'CreationDate': (datetime.now() - timedelta(days=random.randint(1, 365))).isoformat(),
                    'Attachments': [{'InstanceId': instance['InstanceId']}],
                    'Tags': [
                        {'Key': 'Name', 'Value': f'unencrypted-volume-{instance["InstanceId"]}'}
                    ]
                }
                volumes.append(unencrypted_volume)
        
        # 孤兒磁碟 (問題7)
        for i in range(5):
            orphaned_volume = {
                'VolumeId': _generate_aws_id('vol'),
                'Size': random.randint(20, 100),
                'VolumeType': random.choice(['gp2', 'gp3']),
                'State': 'available',  # 問題：可用但未附加
                'Encrypted': True,
                'Iops': random.randint(100, 3000),
                'CreationDate': (datetime.now() - timedelta(days=random.randint(1, 365))).isoformat(),
                'Attachments': [],
                'Tags': [
                    {'Key': 'Name', 'Value': f'orphaned-volume-{i+1}'}
                ]
            }
            volumes.append(orphaned_volume)
        
        # 未加密的孤兒磁碟 (問題8)
        for i in range(3):
            unencrypted_orphaned_volume = {
                'VolumeId': _generate_aws_id('vol'),
                'Size': random.randint(20, 100),
                'VolumeType': random.choice(['gp2', 'gp3']),
                'State': 'available',  # 問題：可用但未附加
                'Encrypted': False,  # 問題：未加密
                'Attachments': [],
                'Tags': [
                    {'Key': 'Name', 'Value': f'unencrypted-orphaned-volume-{i+1}'}
                ]
            }
            volumes.append(unencrypted_orphaned_volume)
        
        return volumes
    
    def _generate_security_rules(self, security_groups: List[Dict]) -> List[Dict]:
        """生成安全規則"""
        security_rules = []
        for sg in security_groups:
            for perm in sg.get('IpPermissions', []):
                rule = {
                    'RuleId': _generate_aws_id('rule'),
                    'GroupId': sg['GroupId'],
                    'Protocol': perm.get('IpProtocol', 'tcp'),
                    'PortRange': f"{perm.get('FromPort', 0)}-{perm.get('ToPort', 0)}",
                    'SourceCIDR': perm['IpRanges'][0]['CidrIp'] if perm.get('IpRanges') else '0.0.0.0/0',
                    'Direction': 'inbound',
                    'Action': 'allow',
                    'Description': f"Rule for {sg['GroupName']}"
                }
                security_rules.append(rule)
        return security_rules


def main():
    """主函數"""
    generator = EnhancedSecurityDataGenerator()
    dataset = generator.generate_complete_dataset()
    
    # 儲存到檔案
    output_file = 'data/raw/mock_aws_resources.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(dataset, f, indent=2, ensure_ascii=False)
    
    print(f"增強版安全測試資料已儲存至: {output_file}")
    print("包含以下安全問題：")
    print("1. 過度寬鬆的安全群組規則")
    print("2. 暴露的 SSH 服務")
    print("3. 暴露的 RDP 服務")
    print("4. 未使用的安全群組 (多個)")
    print("5. 未加密的 EBS 磁碟")
    print("6. 孤兒 EBS 磁碟")
    print("7. 未加密的孤兒 EBS 磁碟")


if __name__ == '__main__':
    main()
