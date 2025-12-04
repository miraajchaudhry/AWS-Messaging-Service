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


async function signup() {
    const email = document.getElementById("email").value.trim();
    const password = document.getElementById("password").value.trim();

    const attributeList = [
        new AmazonCognitoIdentity.CognitoUserAttribute({
            Name: "email",
            Value: email
        })
    ];

    userPool.signUp(email, password, attributeList, null, (err, result) => {
        if (err) {
            alert(err.message || JSON.stringify(err));
            return;
        }

        alert("Signup successful. Check your email for confirmation code.");
        window.location.href = "confirm.html?email=" + encodeURIComponent(email);
    });
}
