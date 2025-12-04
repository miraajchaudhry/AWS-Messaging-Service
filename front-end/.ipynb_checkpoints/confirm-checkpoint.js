const config = {
    region: "us-east-1",
    userPoolId: "us-east-1_222mvHFqQ",
    userPoolClientId: "3a6uhb892lnilc37vblunhnokl",
    wsUrl: "wss://rt0tfsc8b0.execute-api.us-east-1.amazonaws.com/prod"
};

const poolData = {
    UserPoolId: config.userPoolId,
    ClientId: config.userPoolClientId
};

const userPool = new AmazonCognitoIdentity.CognitoUserPool(poolData);

function confirmUser() {
    const email = document.getElementById("email").value.trim();
    const code = document.getElementById("code").value.trim();

    const userData = {
        Username: email,
        Pool: userPool
    };

    const cognitoUser = new AmazonCognitoIdentity.CognitoUser(userData);

    cognitoUser.confirmRegistration(code, true, (err, result) => {
        if (err) {
            alert(err.message || JSON.stringify(err));
            return;
        }
        alert("Your account has been confirmed! You will be taken to the chatroom...");
        window.location.href = "chat.html";
    });
}
