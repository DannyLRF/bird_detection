// Cognito configuration
const poolData = {
    UserPoolId: AWS_CONFIG.cognito.userPoolId,
    ClientId: AWS_CONFIG.cognito.userPoolWebClientId
};

const userPool = new AmazonCognitoIdentity.CognitoUserPool(poolData);
let currentUser = null;

// Check authentication state on page load
document.addEventListener('DOMContentLoaded', function() {
    checkAuthState();
});

// Check authentication state
function checkAuthState() {
    const cognitoUser = userPool.getCurrentUser();
    
    if (cognitoUser != null) {
        cognitoUser.getSession(function(err, session) {
            if (err) {
                console.log('Session error:', err);
                showAuthSection();
                return;
            }
            
            if (session.isValid()) {
                currentUser = cognitoUser;
                setupAWSCredentials(session);
                showMainApp();
            } else {
                showAuthSection();
            }
        });
    } else {
        showAuthSection();
    }
}

// Setup AWS credentials
function setupAWSCredentials(session) {
    const idToken = session.getIdToken().getJwtToken();
    
    AWS.config.region = AWS_CONFIG.region;
    AWS.config.credentials = new AWS.CognitoIdentityCredentials({
        IdentityPoolId: AWS_CONFIG.cognito.identityPoolId,
        Logins: {
            [`cognito-idp.${AWS_CONFIG.region}.amazonaws.com/${AWS_CONFIG.cognito.userPoolId}`]: idToken
        }
    });
    
    // Refresh credentials
    AWS.config.credentials.refresh((error) => {
        if (error) {
            console.error('Credentials refresh error:', error);
        } else {
            console.log('AWS credentials refreshed successfully');
        }
    });
}

// Show authentication section
function showAuthSection() {
    hideLoading();
    document.getElementById('authSection').style.display = 'block';
    document.getElementById('mainApp').style.display = 'none';
    document.getElementById('navbar').style.display = 'none';
}

// Show main application
function showMainApp() {
    hideLoading();
    document.getElementById('authSection').style.display = 'none';
    document.getElementById('mainApp').style.display = 'block';
    document.getElementById('navbar').style.display = 'block';
    
    // Display user information
    if (currentUser) {
        currentUser.getUserAttributes(function(err, attributes) {
            if (!err && attributes) {
                const givenName = attributes.find(attr => attr.getName() === 'given_name');
                const familyName = attributes.find(attr => attr.getName() === 'family_name');
                
                if (givenName && familyName) {
                    document.getElementById('userName').textContent = 
                        `${givenName.getValue()} ${familyName.getValue()}`;
                }
            }
        });
    }
    
    // Show upload section by default
    showSection('upload');
}

// Handle login
function handleLogin(event) {
    event.preventDefault();
    showLoading();
    
    const email = document.getElementById('loginEmail').value;
    const password = document.getElementById('loginPassword').value;
    
    const authenticationData = {
        Username: email,
        Password: password
    };
    
    const authenticationDetails = new AmazonCognitoIdentity.AuthenticationDetails(authenticationData);
    const cognitoUser = new AmazonCognitoIdentity.CognitoUser({
        Username: email,
        Pool: userPool
    });
    
    cognitoUser.authenticateUser(authenticationDetails, {
        onSuccess: function(session) {
            console.log('Login successful');
            currentUser = cognitoUser;
            setupAWSCredentials(session);
            showMainApp();
            showToast(MESSAGES.auth.loginSuccess, 'success');
        },
        onFailure: function(err) {
            console.error('Login failed:', err);
            hideLoading();
            showToast(MESSAGES.auth.loginFailed + err.message, 'error');
        },
        newPasswordRequired: function(userAttributes, requiredAttributes) {
            hideLoading();
            showToast(MESSAGES.auth.passwordRequired, 'warning');
            // TODO: Add new password setup logic here
        }
    });
}

// Handle signup
function handleSignup(event) {
    event.preventDefault();
    showLoading();
    
    const firstName = document.getElementById('signupFirstName').value;
    const lastName = document.getElementById('signupLastName').value;
    const email = document.getElementById('signupEmail').value;
    const password = document.getElementById('signupPassword').value;
    
    const attributeList = [
        new AmazonCognitoIdentity.CognitoUserAttribute({
            Name: 'email',
            Value: email
        }),
        new AmazonCognitoIdentity.CognitoUserAttribute({
            Name: 'given_name',
            Value: firstName
        }),
        new AmazonCognitoIdentity.CognitoUserAttribute({
            Name: 'family_name',
            Value: lastName
        })
    ];
    
    userPool.signUp(email, password, attributeList, null, function(err, result) {
        hideLoading();
        
        if (err) {
            console.error('Signup failed:', err);
            showToast(MESSAGES.auth.signupFailed + err.message, 'error');
            return;
        }
        
        console.log('Signup successful');
        currentUser = result.user;
        showVerificationForm();
        showToast(MESSAGES.auth.signupSuccess, 'success');
    });
}

// Handle email verification
function handleVerification(event) {
    event.preventDefault();
    showLoading();
    
    const verificationCode = document.getElementById('verificationCode').value;
    
    if (!currentUser) {
        hideLoading();
        showToast('User information lost, please register again', 'error');
        return;
    }
    
    currentUser.confirmRegistration(verificationCode, true, function(err, result) {
        hideLoading();
        
        if (err) {
            console.error('Verification failed:', err);
            showToast(MESSAGES.auth.verificationFailed + err.message, 'error');
            return;
        }
        
        console.log('Verification successful');
        showLogin();
        showToast(MESSAGES.auth.verificationSuccess, 'success');
    });
}

// Logout function
function logout() {
    if (currentUser) {
        currentUser.signOut();
        currentUser = null;
    }
    
    // Clear AWS credentials
    AWS.config.credentials = null;
    
    showAuthSection();
    showToast(MESSAGES.auth.logoutSuccess, 'success');
}

// Switch to signup form
function showSignup() {
    document.getElementById('loginForm').style.display = 'none';
    document.getElementById('signupForm').style.display = 'block';
    document.getElementById('verificationForm').style.display = 'none';
}

// Switch to login form
function showLogin() {
    document.getElementById('loginForm').style.display = 'block';
    document.getElementById('signupForm').style.display = 'none';
    document.getElementById('verificationForm').style.display = 'none';
}

// Show verification form
function showVerificationForm() {
    document.getElementById('loginForm').style.display = 'none';
    document.getElementById('signupForm').style.display = 'none';
    document.getElementById('verificationForm').style.display = 'block';
}

// Get current user JWT token
function getCurrentUserToken() {
    return new Promise((resolve, reject) => {
        if (!currentUser) {
            reject('No current user');
            return;
        }
        
        currentUser.getSession(function(err, session) {
            if (err) {
                reject(err);
                return;
            }
            
            if (session.isValid()) {
                resolve(session.getIdToken().getJwtToken());
            } else {
                reject('Invalid session');
            }
        });
    });
}