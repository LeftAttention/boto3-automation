import time
import logging

logger = logging.getLogger(__name__)

def create_load_balancer(elb_v2_client, subnets, elb_name, security_group_ids):

    response = elb_v2_client.create_load_balancer(
        Name=elb_name,
        Subnets=subnets,
        SecurityGroups=security_group_ids,
        Scheme='internet-facing',
        Type='application'
    )
    lb_arn = response['LoadBalancers'][0]['LoadBalancerArn']
    logger.info(f"Load Balancer Created: {lb_arn}")
    return lb_arn, response['LoadBalancers'][0]['DNSName']

def wait_for_load_balancer(elb_v2_client, lb_arn):
    logger.info("Waiting for Load Balancer to become available...")
    waiter = elb_v2_client.get_waiter('load_balancer_available')
    waiter.wait(LoadBalancerArns=[lb_arn])
    logger.info("Load Balancer is now available.")

def create_target_group(elb_v2_client, name, vpc_id):
    response = elb_v2_client.create_target_group(
        Name=name,
        Protocol='HTTP',
        Port=80,
        VpcId=vpc_id,
        HealthCheckProtocol='HTTP',
        HealthCheckPath='/',
        TargetType='instance'
    )
    tg_arn = response['TargetGroups'][0]['TargetGroupArn']
    logger.info(f"Target Group Created: {tg_arn}")
    return tg_arn

def create_launch_configuration(asg_client, lc_name, ami_id, instance_type, key_name, security_group_ids):
    asg_client.create_launch_configuration(
        LaunchConfigurationName=lc_name,
        ImageId=ami_id,
        InstanceType=instance_type,
        KeyName=key_name,
        SecurityGroups=security_group_ids,
    )
    logger.info(f"Launch Configuration Created: {lc_name}")
    # Boto3 does not have a waiter for launch configuration, so we use a brief pause
    time.sleep(10)  # Adjust based on your needs
    return lc_name

def create_auto_scaling_group(asg_client, asg_name, lc_name, tg_arn, subnets_string):
    asg_client.create_auto_scaling_group(
        AutoScalingGroupName=asg_name,
        LaunchConfigurationName=lc_name,
        MinSize=1,
        MaxSize=3,
        DesiredCapacity=3,
        TargetGroupARNs=[tg_arn],
        VPCZoneIdentifier=subnets_string
    )
    logger.info(f"Auto Scaling Group Created: {asg_name}")
    # Boto3 does not have a direct waiter for ASG instances to be in service, so we implement a custom wait
    # or simply give a fixed time for instances to launch and register with the load balancer
    time.sleep(60)  # Adjust based on your needs