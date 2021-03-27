import boto3


class S3Utils:
    def __init__(self, role_to_assume=None):
        if role_to_assume:
            sts_client = boto3.client('sts')
            assumed_role_object = sts_client.assume_role(
                RoleArn=role_to_assume,
                RoleSessionName='AssumeRoleSession1'
            )
            self.credentials = assumed_role_object['Credentials']
            self.s3 = boto3.client(
                's3',
                aws_access_key_id=self.credentials['AccessKeyId'],
                aws_secret_access_key=self.credentials['SecretAccessKey'],
                aws_session_token=self.credentials['SessionToken'],
            )
        else:
            self.s3 = boto3.client('s3')  # use keys from env_variables

    def file_obj_to_s3(self, file_obj, s3_file, bucket):
        self.s3.upload_fileobj(Fileobj=file_obj, Key=s3_file, Bucket=bucket)

    def s3_obj_to_bytes(self, s3_file, bucket):
        body = self.s3.get_object(Bucket=bucket, Key=s3_file)['Body']
        return body.read()

