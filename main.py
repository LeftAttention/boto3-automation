import boto3
from omegaconf import OmegaConf
import pprint
import time

from utils.logger import create_logger
from utils.comm import read_script
from utils import ec2, elb, lambda_utils, monitor, autoscaling

def main():

    config_path = "config.yaml"
    cfg = OmegaConf.load(config_path)

    logger = create_logger(cfg)
    logger.info(pprint.pformat(cfg))

    # Initialize Boto3 EC2 client
    ec2_client = boto3.client('ec2', region_name=cfg.aws_config.region)
    elb_v2_client = boto3.client('elbv2', region_name=cfg.aws_config.region)
    autoscaling_client = boto3.client('autoscaling', region_name=cfg.aws_config.region)
    sns_client = boto3.client('sns', region_name=cfg.aws_config.region)
    cloudwatch_client = boto3.client('cloudwatch', region_name=cfg.aws_config.region)
    lambda_client = boto3.client('lambda', region_name=cfg.aws_config.region)
    events_client = boto3.client('events', region_name=cfg.aws_config.region)


    user_data_script = read_script(cfg.aws_config.ec2_config.user_data_script_file_path)

    logger.info(pprint.pformat(user_data_script))

    instance_id = ec2.launch_ec2_instance_with_user_data(
        ec2_client=ec2_client,
        script_contents=user_data_script,
        instance_name=cfg.aws_config.ec2_config.instance_name,
        ami_id=cfg.aws_config.ec2_config.new_instance_ami_id,
        instance_type=cfg.aws_config.ec2_config.new_instance_type,
        key_name=cfg.aws_config.ec2_config.key_name,
        security_group_ids=list(cfg.aws_config.ec2_config.security_group_ids),
        subnet_id=cfg.aws_config.ec2_config.subnet_id,
    )

    # instance_id = cfg.aws_config.reuse_ec2_config.instance_id

    if instance_id:
        logger.info(f"Waiting for instance {instance_id} to start")
        ec2.wait_for_instance_initialization(ec2_client, instance_id)
        logger.info(f"Instance {instance_id} started")

        logger.info(f"Creating AMI")
        image_id = ec2.create_ami_from_instance(ec2_client, instance_id, cfg.aws_config.ec2_config.ami_name)
        if image_id:
            logger.info(f"Waiting for AMI {image_id} to start")

            ec2.wait_for_ami_creation(ec2_client, image_id)
            logger.info(f"AMI {image_id} started")

    lb_arn, lb_dns_name = elb.create_load_balancer(
        elb_v2_client, 
        subnets=list(cfg.aws_config.elb_config.subnets), 
        elb_name=cfg.aws_config.elb_config.name, 
        security_group_ids=list(cfg.aws_config.elb_config.security_group_ids)
    )

    elb.wait_for_load_balancer(
        elb_v2_client, lb_arn
    )

    tg_arn = elb.create_target_group(
        elb_v2_client, 
        name=cfg.aws_config.elb_config.target_group_name, 
        vpc_id=cfg.aws_config.elb_config.vpc_id
    )

    lc_name = autoscaling.create_launch_configuration(
        autoscaling_client, 
        lc_name=cfg.aws_config.asg_config.lc_name, 
        ami_id=cfg.aws_config.reuse_ec2_config.ami_id, 
        instance_type=cfg.aws_config.ec2_config.new_instance_type, 
        key_name=cfg.aws_config.ec2_config.key_name, 
        security_group_ids=list(cfg.aws_config.ec2_config.security_group_ids)
    )

    autoscaling.create_auto_scaling_group(
        autoscaling_client,
        asg_name=cfg.aws_config.asg_config.name,
        lc_name=lc_name,
        tg_arn=tg_arn,
        subnets_string=','.join(list(cfg.aws_config.elb_config.subnets))
    )

    topic_arn = monitor.create_sns_topic(
        sns_client, 
        cfg.aws_config.monitor.sns_topic
    )

    monitor.subscribe_to_topic(sns_client, topic_arn, cfg.aws_config.monitor.email)

    time.sleep(60)

    monitor.create_cpu_utilization_alarm_for_asg(
        cloudwatch_client, 
        alarm_name=cfg.aws_config.monitor.alarm_name, 
        asg_name=cfg.aws_config.asg_config.name, 
        topic_arn=topic_arn,
    )

    time.sleep(60)

    function_arn = lambda_utils.create_lambda_function(
        lambda_client, 
        function_name=cfg.aws_config.lambda_cfg.function_name, 
        zip_file_path=cfg.aws_config.lambda_cfg.zip_file_path, 
        role_arn=cfg.aws_config.lambda_cfg.role_arn
    )

    rule_arn = monitor.create_cloudwatch_events_rule(
        events_client, 
        rule_name=cfg.aws_config.monitor.rule_name, 
        schedule_expression=cfg.aws_config.monitor.schedule_expression
    )

    monitor.add_lambda_target_to_rule(
        events_client, 
        cfg.aws_config.monitor.rule_name, 
        function_arn
    )

    lambda_client.add_permission(
        FunctionName=cfg.aws_config.lambda_cfg.function_name,
        StatementId='CloudWatchEventsInvocation',  # An identifier for the statement
        Action='lambda:InvokeFunction',
        Principal='events.amazonaws.com',
        SourceArn=rule_arn,
    )

    autoscaling.create_target_tracking_policy(
        autoscaling_client, 
        asg_name=cfg.aws_config.asg_config.name, 
        policy_name=cfg.aws_config.asg_config.policy_name,
        target_cpu_utilization=cfg.aws_config.asg_config.cpu_utilization
    )


    autoscaling.create_simple_scaling_policy(
        autoscaling_client,
        asg_name=cfg.aws_config.asg_config.name, 
        policy_name_simple=cfg.aws_config.asg_config.policy_name_simple, 
        adjustment_type=cfg.aws_config.asg_config.adjustment_type, 
        scaling_adjustment=cfg.aws_config.asg_config.scaling_adjustment, 
        cooldown=cfg.aws_config.asg_config.cooldown
    )







if __name__ == "__main__":
    main()