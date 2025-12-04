from aws_cdk import (
    # Duration,
    Stack,
    aws_apigatewayv2 as apigwv2,
    aws_apigatewayv2_integrations as apigw_integrations,
    aws_lambda as _lambda,
    aws_s3 as s3,
    aws_s3_deployment as s3deploy,
    aws_dynamodb as dynamodb,
    aws_iam as iam,
    CfnOutput
)
from constructs import Construct

class Group9ImsStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # The code that defines your stack goes here
        # Lambdas
        on_connect = _lambda.Function(
            self, "OnConnectFunction",
            runtime=_lambda.Runtime.NODEJS_16_X,
            handler="index.handler",
            code=_lambda.Code.from_asset("lambda")
        )

        on_disconnect = _lambda.Function(
            self, "OnDisconnectFunction",
            runtime=_lambda.Runtime.NODEJS_16_X,
            handler="index.handler",
            code=_lambda.Code.from_asset("lambda")
        )

        send_message = _lambda.Function(
            self, "SendMessageFunction",
            runtime=_lambda.Runtime.NODEJS_16_X,
            handler="index.handler",
            code=_lambda.Code.from_asset("lambda")
        )

        get_upload_url = _lambda.Function(
            self, "GetUploadURLFunction",
            runtime=_lambda.Runtime.NODEJS_16_X,
            handler="index.handler",
            code=_lambda.Code.from_asset("lambda")
        )

        join_room = _lambda.Function(
            self, "JoinRoomFunction",
            runtime=_lambda.Runtime.NODEJS_16_X,
            handler="index.handler",
            code=_lambda.Code.from_asset("lambda")
        )

        table = dynamodb.Table.from_table_name(
        self,
        "ImportedCCGroup9Table",
        "CCGroup9Table"
    )
        table.grant_read_write_data(on_connect)
        table.grant_read_write_data(on_disconnect)
        table.grant_read_write_data(send_message)
        table.grant_read_write_data(get_upload_url)
        table.grant_read_write_data(join_room)


        # front end
        bucket = s3.Bucket(self, "FrontendBucket",
                website_index_document="index.html",
                public_read_access=True,
                block_public_access=s3.BlockPublicAccess(
                        block_public_policy=False,
                        block_public_acls=False,
                        ignore_public_acls=False,
                        restrict_public_buckets=False
                )
        )

        bucket.grant_read_write(get_upload_url)

        s3deploy.BucketDeployment(self, "DeployFrontend",
            sources=[s3deploy.Source.asset("../group9_ims/front-end")],
            destination_bucket=bucket
        )

        

        CfnOutput(self, "WebsiteURL", value=bucket.bucket_website_url)

        websocket_api = apigwv2.WebSocketApi(
            self, "group9_IMServiceAPI",
            route_selection_expression="$request.body.action"
        )

        # Integrations
        connect_integration = apigw_integrations.WebSocketLambdaIntegration(
            "ConnectIntegration", on_connect
        )
        disconnect_integration = apigw_integrations.WebSocketLambdaIntegration(
            "DisconnectIntegration", on_disconnect
        )
        send_message_integration = apigw_integrations.WebSocketLambdaIntegration(
            "SendMessageIntegration", send_message
        )
        get_upload_url_integration = apigw_integrations.WebSocketLambdaIntegration(
            "GetUploadURLIntegration", get_upload_url
        )
        join_room_integration = apigw_integrations.WebSocketLambdaIntegration(
            "GetUploadURLIntegration", join_room
        )

        # Routes
        websocket_api.add_route("$connect", integration=connect_integration)
        websocket_api.add_route("$disconnect", integration=disconnect_integration)
        websocket_api.add_route("sendMessage", integration=send_message_integration)
        websocket_api.add_route("getUploadUrl", integration=get_upload_url_integration)
        websocket_api.add_route("joinRoom", integration=join_room_integration)

        # Stage
        stage = apigwv2.WebSocketStage(
            self, "IMServideStage",
            web_socket_api=websocket_api,
            stage_name="prod",
            auto_deploy=True
        )

        manage_conn_policy = iam.PolicyStatement(
            effect=iam.Effect.ALLOW,
            actions=["execute-api:ManageConnections"],
            resources=[
                f"arn:aws:execute-api:{self.region}:{self.account}:{websocket_api.api_id}/{stage.stage_name}/POST/@connections/*"
            ]
        )

        send_message.add_to_role_policy(manage_conn_policy)
        join_room.add_to_role_policy(manage_conn_policy)
        on_disconnect.add_to_role_policy(manage_conn_policy)


        # Output the WebSocket URL
        CfnOutput(
            self, "WebSocketURL",
            value=stage.url
        )

        CfnOutput(
            self, "WebSocketCallbackURL",
            value=stage.callback_url
        )

        
        # example resource
        # queue = sqs.Queue(
        #     self, "Group9ImsQueue",
        #     visibility_timeout=Duration.seconds(300),
        # )
