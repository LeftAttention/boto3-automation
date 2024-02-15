import logging

logger = logging.getLogger(__name__)

def create_sns_topic(sns_client, topic_name):
    response = sns_client.create_topic(Name=topic_name)
    topic_arn = response['TopicArn']
    logger.info(f"SNS Topic Created: {topic_arn}")
    return topic_arn

def subscribe_to_topic(sns_client, topic_arn, email):
    response = sns_client.subscribe(
        TopicArn=topic_arn,
        Protocol='email',
        Endpoint=email
    )
    logger.info(f"Subscription added to topic. Check {email} to confirm subscription.")
    return response


def create_cpu_utilization_alarm(cloudwatch_client, alarm_name, instance_id, topic_arn):
    cloudwatch_client.put_metric_alarm(
        AlarmName=alarm_name,
        ComparisonOperator='GreaterThanThreshold',
        EvaluationPeriods=1,
        MetricName='CPUUtilization',
        Namespace='AWS/EC2',
        Period=300,
        Statistic='Average',
        Threshold=70.0,  # Set to the desired CPU utilization threshold
        ActionsEnabled=True,
        AlarmActions=[
            topic_arn  # SNS topic ARN to notify when the alarm state changes
        ],
        AlarmDescription='Alarm when server CPU exceeds 70%',
        Dimensions=[
            {
              'Name': 'InstanceId',
              'Value': instance_id
            },
        ]
    )
    logger.info(f"CloudWatch Alarm '{alarm_name}' created for instance '{instance_id}'.")

def create_cpu_utilization_alarm_for_asg(cloudwatch_client, alarm_name, asg_name, topic_arn):
    cloudwatch_client.put_metric_alarm(
        AlarmName=alarm_name,
        ComparisonOperator='GreaterThanThreshold',
        EvaluationPeriods=1,  # The number of periods over which data is compared to the specified threshold.
        MetricName='CPUUtilization',
        Namespace='AWS/EC2',
        Period=300,  # The period in seconds over which the specified statistic is applied. Must be a multiple of 60.
        Statistic='Average',
        Threshold=70.0,  # Set to the desired CPU utilization threshold
        ActionsEnabled=True,
        AlarmActions=[
            topic_arn  # SNS topic ARN to notify when the alarm state changes
        ],
        AlarmDescription='Alarm when ASG CPU exceeds 70%',
        Dimensions=[
            {
              'Name': 'AutoScalingGroupName',
              'Value': asg_name
            },
        ]
    )
    logger.info(f"CloudWatch Alarm '{alarm_name}' created for ASG '{asg_name}'.")

def create_cloudwatch_events_rule(events_client, rule_name, schedule_expression):
    response = events_client.put_rule(
        Name=rule_name,
        ScheduleExpression=schedule_expression,  # e.g., 'rate(5 minutes)'
        State='ENABLED',
        Description='Triggers the Lambda function periodically',
    )
    
    logger.info(f"CloudWatch Events rule '{rule_name}' created successfully.")
    return response['RuleArn']

# Function to add the Lambda function as the target for the CloudWatch Events rule
def add_lambda_target_to_rule(events_client, rule_name, function_arn):
    response = events_client.put_targets(
        Rule=rule_name,
        Targets=[
            {
                'Id': '1',  # An arbitrary unique ID for the target
                'Arn': function_arn,
            },
        ]
    )
    
    logger.info(f"Lambda function '{function_arn}' added as a target to the rule '{rule_name}'.")
