import aws_cdk as core
import aws_cdk.assertions as assertions

from group9_ims.group9_ims_stack import Group9ImsStack

# example tests. To run these tests, uncomment this file along with the example
# resource in group9_ims/group9_ims_stack.py
def test_sqs_queue_created():
    app = core.App()
    stack = Group9ImsStack(app, "group9-ims")
    template = assertions.Template.from_stack(stack)

#     template.has_resource_properties("AWS::SQS::Queue", {
#         "VisibilityTimeout": 300
#     })
