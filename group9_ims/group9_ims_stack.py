import aws_cdk as cdk
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
    aws_cloudfront as cf,
    aws_cloudfront_origins as cf_origins,
    CfnOutput
)

from constructs import Construct

class Group9ImsStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # The code that defines your stack goes here
        # Lambda functions' constructs
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

        # Make Dymamo DB table
        table = dynamodb.Table.from_table_name(
           self, "ImportedCCGroup9Table",
           "CCGroup9Table"
        )

        # give correct lambdas permission to read/write to table
        table.grant_read_write_data(on_connect)
        table.grant_read_write_data(on_disconnect)
        table.grant_read_write_data(send_message)
        table.grant_read_write_data(get_upload_url)
        table.grant_read_write_data(join_room)

        # S3 bucket for front end
        front_end_bucket = s3.Bucket(
            self, "FrontEndBucket",
            public_read_access=False,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            removal_policy=cdk.RemovalPolicy.DESTROY
        )

        # deploy correct files into bucket
        s3deploy.BucketDeployment(self, "DeployFrontend",
            sources=[s3deploy.Source.asset("../group9_ims/front-end")],
            destination_bucket=front_end_bucket
        )

        # make access identity
        oai = cf.OriginAccessIdentity(
            self, "FrontEndOAI"
        )

        # set origin
        s3_origin = cf_origins.S3BucketOrigin.with_origin_access_identity(
            front_end_bucket, origin_access_identity=oai
        )

        distribution = cf.Distribution(
            self, "FrontEnd",
            default_behavior=cf.BehaviorOptions(
                origin=s3_origin,
                viewer_protocol_policy=cf.ViewerProtocolPolicy.REDIRECT_TO_HTTPS
            ),
            default_root_object="index.html",
            error_responses=[
                cf.ErrorResponse(
                    http_status=404,
                    response_page_path="/notfound.html",
                    response_http_status=404
                )
            ]
        )

        # Allow access identity to access bucket and its contents
        front_end_bucket.add_to_resource_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=["s3:ListBucket"],
                principals=[oai.grant_principal],
                resources=[front_end_bucket.bucket_arn]
            )
        )   

        front_end_bucket.add_to_resource_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=["s3:GetObject"],
                principals=[oai.grant_principal],
                resources=[front_end_bucket.arn_for_objects("*")]
            )
        )

        # Output website url
        CfnOutput(
            self, "Website_URL",
            value="https://" + distribution.distribution_domain_name
        )

        # Set Websocket API
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
