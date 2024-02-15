import base64

import logging

logger = logging.getLogger(__name__)

def get_instance_user_data(ec2_client, instance_id):
    try:
        # Describe instance attribute (UserData)
        response = ec2_client.describe_instance_attribute(InstanceId=instance_id, Attribute='userData')
        
        # Extract and decode user data
        user_data_encoded = response.get('UserData', {}).get('Value', '')
        if user_data_encoded:
            user_data_decoded = base64.b64decode(user_data_encoded).decode('utf-8')
            return user_data_decoded
        else:
            return "No user data found for this instance."
    except Exception as e:
        return f"Error retrieving user data: {e}"

def launch_ec2_instance_with_user_data(
        ec2_client, script_contents,
        ami_id, instance_type, key_name,
        security_group_ids, subnet_id,
        instance_name
):
    try:
        response = ec2_client.run_instances(
            ImageId=ami_id,
            InstanceType=instance_type,
            KeyName=key_name,
            SecurityGroupIds=security_group_ids,
            SubnetId=subnet_id,
            UserData=script_contents,
            MinCount=1,
            MaxCount=1,
            TagSpecifications=[
                {
                    'ResourceType': 'instance',
                    'Tags': [
                        {
                            'Key': 'Name',
                            'Value': instance_name
                        }
                    ]
                }
            ]
        )
        instance_id = response['Instances'][0]['InstanceId']
        logger.info(f"EC2 instance launched successfully: {instance_id}")
        return instance_id
    except Exception as e:
        logger.error(f"Error launching EC2 instance: {e}")
        return None

def create_ami_from_instance(ec2_client, instance_id, ami_name):
    try:
        response = ec2_client.create_image(InstanceId=instance_id, Name=ami_name)
        image_id = response['ImageId']
        print(f"AMI creation started: {image_id}")
        return image_id
    except Exception as e:
        print(f"Error creating AMI: {e}")
        return None
    
def wait_for_instance_initialization(ec2_client, instance_id):
    waiter = ec2_client.get_waiter('instance_status_ok')
    logger.info("Waiting for instance to be initialized...")
    waiter.wait(InstanceIds=[instance_id])
    logger.info("Instance is initialized.")

def wait_for_ami_creation(ec2_client, image_id):
    waiter = ec2_client.get_waiter('image_available')
    print("Waiting for AMI to be available...")
    waiter.wait(ImageIds=[image_id])
    print("AMI is available.")