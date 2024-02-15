
def create_lambda_function(lambda_client, function_name, zip_file_path, role_arn):
    with open(zip_file_path, 'rb') as f:
        zip_file_bytes = f.read()
    
    response = lambda_client.create_function(
        FunctionName=function_name,
        Runtime='python3.8',  # Specify the runtime
        Role=role_arn,  # The ARN of the IAM role that Lambda assumes when it executes your function
        Handler='lambda_function.lambda_handler',  # The name of the function (file.method)
        Code={
            'ZipFile': zip_file_bytes,
        },
        Description='A Lambda function triggered by CloudWatch Events.',
        Timeout=15,  # Function execution time at which AWS Lambda should terminate the function (seconds)
        MemorySize=128,  # Amount of memory available to the function (MB)
    )
    
    print(f"Lambda function '{function_name}' created successfully.")
    return response['FunctionArn']