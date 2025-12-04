/*
    AWS Lambda Handler
    Cloud Computing Final Project - Group 9 (Miraaj, Connor, Kaushik, Emma, Michael)
    Project - Instant Messaging Service
    File Created By - Emma Crowe

This manages user connections ($connect, $disconnect) and stores the messages and connection data in the CCGroup9Table, then generates secure S3 pre-signed URLs to allow users to upload images and videos.

All sources of help come from the AWS Documentation!
*/

const AWS = require("aws-sdk");
const ddb = new AWS.DynamoDB.DocumentClient();

const TABLE_NAME = "CCGroup9Table";
const s3 = new AWS.S3();
const S3_BUCKET = "cc-group9-chat-media"; // has to be created when using


exports.handler = async (event) => {
    try {
        console.log("EVENT:", JSON.stringify(event, null, 2));

        const route = event.requestContext.routeKey;
        let body = event.body;

        if (typeof body === "string") {
            try { body = JSON.parse(body); } catch {}
        }

        if (route === "$connect") return handleConnect(event);
        if (route === "$disconnect") return handleDisconnect(event);
        if (route === "sendMessage" || body?.action === "sendMessage")
            return handleSendMessage(event, body);
        if (route === "getUploadUrl" || body?.action === "getUploadUrl")
            return handleGetUploadUrl(event, body);
        if (route === "joinRoom" || body?.action === "$joinRoom")
            return handleJoinRoom(event, body);

        return { statusCode: 200, body: "OK" };

    } catch (err) {
        console.error(err);
        return { statusCode: 500, body: err.message };
    }
};


// $connect — store connection in CCGroup9Table
async function handleConnect(event) {
    const connectionId = event.requestContext.connectionId;
    const userId = event.requestContext.authorizer?.claims?.sub || "UnknownUser";

    const timestamp = `${Date.now()}`;

    await ddb.put({
        TableName: TABLE_NAME,
        Item: {
            Connection_ID: connectionId,
            Time: timestamp,      // Sort key MUST be a string
            User_ID: userId,
            Message: "CONNECTED"
        }
    }).promise();

    console.log(`Stored connection ${connectionId} at Time ${timestamp}`);

    return { statusCode: 200, body: "connected" };
}


// $disconnect — delete all rows for a connectionId
async function handleDisconnect(event) {
    const connectionId = event.requestContext.connectionId;

    const existing = await ddb.query({
        TableName: TABLE_NAME,
        KeyConditionExpression: "Connection_ID = :cid",
        ExpressionAttributeValues: { ":cid": connectionId }
    }).promise();

    for (const item of existing.Items) {
        await ddb.delete({
            TableName: TABLE_NAME,
            Key: {
                Connection_ID: item.Connection_ID,
                Time: item.Time
            }
        }).promise();
    }

    console.log(`Deleted all rows for ${connectionId}`);

    return { statusCode: 200, body: "disconnected" };
}

// joinRoom - save room membership
async function handleJoinRoom(event, body) {
    const connectionId = event.requestContext.connectionId;
    const userId = event.requestContext.authorizer?.claims?.sub || "UnknownUser";
    const roomName = body?.room;

    if(!roomName)
        return { statusCode: 400, body: "Missing room name" };

    await ddb.put({
        TableName: TABLE_NAME,
        Item: {
            Connection_ID: connectionId,
            Time: "JOIN",
            User_ID: userId,
            Message: roomName
        }
    }).promise();

    console.log(`${connectionId} joined room ${roomName}`);

    return {
        statusCode: 200,
        body: JSON.stringify({ joined: true, room: roomName})
    };
}

// sendMessage — insert new message row into CCGroup9Table
async function handleSendMessage(event, body) {
    const connectionId = event.requestContext.connectionId;
    const userId = event.requestContext.authorizer?.claims?.sub || "UnknownUser";

    const timestamp = `${Date.now()}`;
    const messageText = body?.text || body?.message || "";

    // get room

    const joinRow = await ddb.get({
        TableName: TABLE_NAME,
        Key: {
            Connection_ID: connectionId,
            Time: "JOIN"
       }
    }).promise();

    const roomName = joinRow.Item?.Message;

    if (!roomName)
        return { statusCode: 400, body: "User has not joined a room"};

    await ddb.put({
        TableName: TABLE_NAME,
        Item: {
            Connection_ID: connectionId,  // Partition key stays connectionId
            Time: timestamp,              // Sort key
            User_ID: userId,
            Message: messageText
        }
    }).promise();

    const apiGw = new AWS.ApiGatewayManagementApi({
        endpoint: `${event.requestContext.domainName}/${event.requestContext.stage}`
    });

    const allConnections = await ddb.scan({
        TableName: TABLE_NAME,
        FilterExpression: "#t = :join",
        ExpressionAttributeNames: { "#t": "Time"},
        ExpressionAttributeValues: { ":join": "JOIN"}
    }).promise();

    const roomConnections = allConnections.Items.filter(
        item => item.Message === roomName
    );

    for (const conn of roomConnections) {
        await apiGw.postToConnection({
            ConnectionId: conn.Connection_ID,
            Data: JSON.stringify({
                from: userId,
                room: roomName,
                message: messageText,
                timestamp: timestamp
            })
        }).promise().catch(err => {
            if (err.statusCode !== 410) console.log(err);
        });
    }


    console.log(`Stored message at ${timestamp}: ${messageText}`);
    console.log(`Broadcasted message to ${roomConnections.length} users in room ${roomName}`);
    return {
        statusCode: 200,
        body: JSON.stringify({
            saved: true,
            sent: true
        })
    };
}


// getUploadUrl
async function handleGetUploadUrl(event, body) {
    const userId = event.requestContext.authorizer?.claims?.sub || "UnknownUser";
    const fileExt = body?.fileExt || "jpg";
    const mediaKey = `messages/${Date.now()}.${fileExt}`;

    const uploadUrl = s3.getSignedUrl("putObject", {
        Bucket: S3_BUCKET,
        Key: mediaKey,
        ContentType: body?.contentType || "application/octet-stream",
        Expires: 300
    });

    return {
        statusCode: 200,
        body: JSON.stringify({ uploadUrl, mediaKey })
    };
}

