const config = {
    region: "us-east-1",
    userPoolId: "us-east-1_222mvHFqQ",
    userPoolClientId: "3a6uhb892lnilc37vblunhnokl",
    wsUrl: "wss://rt0tfsc8b0.execute-api.us-east-1.amazonaws.com/prod"
};

AWS.config.region = config.region;

const poolData = {
    UserPoolId: config.userPoolId,
    ClientId: config.userPoolClientId
};

const userPool = new AmazonCognitoIdentity.CognitoUserPool(poolData);

function login() {
    const email = document.getElementById("email").value.trim();
    const password = document.getElementById("password").value.trim();

    const authData = {
        Username: email,
        Password: password
    };

    const authDetails = new AmazonCognitoIdentity.AuthenticationDetails(authData);

    const userData = {
        Username: email,
        Pool: userPool
    };

    const cognitoUser = new AmazonCognitoIdentity.CognitoUser(userData);

    cognitoUser.authenticateUser(authDetails, {
        onSuccess: session => {
            const idToken = session.getIdToken().getJwtToken();
            localStorage.setItem("idToken", idToken);
            window.location.href = "chat.html";
        },
        onFailure: err => {
            alert(err.message || JSON.stringify(err));
        }
    });
}
