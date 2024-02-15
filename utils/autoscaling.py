import time
import logging

logger = logging.getLogger(__name__)

def create_launch_configuration(autoscaling_client, lc_name, ami_id, instance_type, key_name, security_group_ids):
    autoscaling_client.create_launch_configuration(
        LaunchConfigurationName=lc_name,
        ImageId=ami_id,
        InstanceType=instance_type,
        KeyName=key_name,
        SecurityGroups=security_group_ids,
    )
    logger.info(f"Launch Configuration Created: {lc_name}")
    # Boto3 does not have a waiter for launch configuration, so we use a brief pause
    time.sleep(30)  # Adjust based on your needs
    return lc_name

def create_auto_scaling_group(autoscaling_client, asg_name, lc_name, tg_arn, subnets_string):
    autoscaling_client.create_auto_scaling_group(
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
    time.sleep(180)  # Adjust based on your needs

def create_target_tracking_policy(autoscaling_client, asg_name, policy_name, target_value, metric_name='CPUUtilization'):
    response = autoscaling_client.put_scaling_policy(
        AutoScalingGroupName=asg_name,
        PolicyName=policy_name,
        PolicyType='TargetTrackingScaling',
        TargetTrackingConfiguration={
            'PredefinedMetricSpecification': {
                'PredefinedMetricType': 'ASGAverageCPUUtilization',
            },
            'TargetValue': target_value,
        },
    )
    print(f"Target tracking scaling policy '{policy_name}' created for ASG '{asg_name}'.")
    return response['PolicyARN']

def create_simple_scaling_policy(autoscaling_client, asg_name, policy_name, adjustment_type, scaling_adjustment, cooldown):
    response = autoscaling_client.put_scaling_policy(
        AutoScalingGroupName=asg_name,
        PolicyName=policy_name,
        PolicyType='Simple',
        AdjustmentType=adjustment_type,  # e.g., 'ChangeInCapacity'
        ScalingAdjustment=scaling_adjustment,  # e.g., 1 or -1
        Cooldown=cooldown,  # The amount of time, in seconds, after a scaling activity completes before any further dynamic scaling activities can start
    )
    print(f"Simple scaling policy '{policy_name}' created for ASG '{asg_name}'.")
    return response['PolicyARN']