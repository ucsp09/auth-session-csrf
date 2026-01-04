const state = {
    isLoggedIn: null,
    sessionId: null,
    csrfToken: null
};

main();

function main(){
    checkLoginStatusAndUpdateState();
    addEventHandlers();
}

function addEventHandlers(){
    addLoginButtonClickEventHandler();
    addLogoutButtonClickEventHandler();
    addViewAllProtectedResourcesButtonClickEventHandler();
}

function addLoginButtonClickEventHandler(){
    const loginButton = document.getElementById("loginButton");
    if(loginButton !== null){
        loginButton.addEventListener("click", loginButtonClickEventHandler);
    }
}

function addLogoutButtonClickEventHandler(){
    const logoutButton = document.getElementById("logoutButton");
    if(logoutButton !== null){
        logoutButton.addEventListener("click", logoutButtonClickEventHandler);
    }
}

function addViewAllProtectedResourcesButtonClickEventHandler(){
    const viewAllProtectedResourcesButton = document.getElementById("viewAllProtectedResourcesButton");
    if(viewAllProtectedResourcesButton !== null){
        viewAllProtectedResourcesButton.addEventListener("click", viewAllProtectedResourcesButtonClickEventHandler);
    }
}

async function callLoginAPI(username, password){
    const loginUrl = "http://localhost:8000/api/v1/login";
    const response = await fetch(loginUrl, {
        method: "POST",
        credentials: "include",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            username: username,
            password: password
        })
    })
    return response;
}

async function callLoginStatusAPI(){
    const loginStatusUrl = "http://localhost:8000/api/v1/login/status";
    const response = await fetch(loginStatusUrl, {
        method: "GET",
        credentials: "include"
    })
    return response;
}

async function callLogoutAPI(){
    const logoutUrl = "http://localhost:8000/api/v1/logout";
    const response = await fetch(logoutUrl, {
        method: "GET",
        credentials: "include"
    })
    return response;
}

async function callGetAllProtectedResourcesAPI(){
    const url = "http://localhost:8000/api/v1/protected/resources";
    const response = await fetch(url, {
        method: "GET",
        credentials: "include",
        headers: {
            "X-CSRF-TOKEN": state.csrfToken
        }
    })
    return response
}

async function setIsLoggedIn(isLoggedIn){
    state.isLoggedIn = isLoggedIn;
}

async function setSessionId(sessionId){
    state.sessionId = sessionId;
}

async function setCsrfToken(csrfToken){
    state.csrfToken = csrfToken;
}

async function checkLoginStatusAndUpdateState(){
    const loginStatusResponse = await callLoginStatusAPI();
    if(!loginStatusResponse.ok){
        setIsLoggedIn(false);
        setSessionId(null);
        setCsrfToken(null);
    }else{
        const data = await loginStatusResponse.json();
        const sessionId = data?.sessionId ?? null;
        const csrfToken = data?.csrfToken ?? null;
        if(sessionId === null){
            console.log("User is not logged in");
            setIsLoggedIn(false);
            setSessionId(null);
            setCsrfToken(null);
        }else{
            console.log("User is logged in");
            setIsLoggedIn(true);
            setSessionId(sessionId);
            setCsrfToken(csrfToken);
        }
    }
    redirectUIBasedOnLoginState();
}

function redirectUIBasedOnLoginState(){
    const loginStatus = state.isLoggedIn;
    console.log(loginStatus);
    if(loginStatus === true){
        if(window.location.pathname === '/ui/login'){
            window.location.replace('/ui/home');
        }else{
            return;
        }
    }else{
        if(window.location.pathname !== '/ui/login'){
            window.location.replace('/ui/login');
        }else{
            return ;
        }
    }
}

function loginButtonClickEventHandler(event){
    event.preventDefault();
    displayLoginForm();
}

async function viewAllProtectedResourcesButtonClickEventHandler(event){
    event.preventDefault();
    const response = await callGetAllProtectedResourcesAPI();
    if(!response.ok){
        displayToast('Unable To View All protected resources', 'failure', 10000);
    }else{
        displayToast('Success', 'success', 10000);
        const data = await response.json();
        const resources = data?.items ?? [];
        displayProtectedResourcesTable(resources);
    }
}

function displayProtectedResourcesTable(resources){
    const protectedResourcesTableRowsElement = document.getElementById("protectedResourcesTableRows");
    protectedResourcesTableRowsElement.replaceChildren();
    for(const resource of resources){
        const resourceRowElement = document.createElement('tr');
        const nameColumnRowElement = document.createElement('td');
        nameColumnRowElement.textContent = resource.name;
        const propertiesColumnRowElement = document.createElement('td');
        propertiesColumnRowElement.textContent = formatProperties(resource.properties);
        resourceRowElement.appendChild(nameColumnRowElement);
        resourceRowElement.appendChild(propertiesColumnRowElement);
        protectedResourcesTableRowsElement.appendChild(resourceRowElement);
    }
}

function formatProperties(properties){
    if (!properties || typeof properties !== "object") {
        return "";
    }
    return Object.entries(properties).map(
        ([key, value]) => 
            `${key}:${value} `).join("");
}

async function logoutButtonClickEventHandler(event){
    event.preventDefault();
    const logoutResponse = await callLogoutAPI();
    if(!logoutResponse.ok){
        window.location.replace(window.location.pathname);
    }else{
        setIsLoggedIn(false);
        setSessionId(null);
        setCsrfToken(null);
        window.location.replace('/ui/login');
    }
}

async function loginFormSubmitEventHandler(event){
    event.preventDefault();
    const username = document.getElementById("username").value;
    const password = document.getElementById("password").value;
    const loginResponse = await callLoginAPI(username, password);
    if(!loginResponse.ok){
        displayToast('Login Failed! Pls Check username and password', 'failure', 10000);
        setIsLoggedIn(false);
        setCsrfToken(null);
        setSessionId(null);
    }else{
        const data = await loginResponse.json();
        const sessionId = data?.sessionId ?? null;
        const csrfToken = data?.csrfToken ?? null;
        if(sessionId === null || csrfToken === null){
            setIsLoggedIn(false);
            setCsrfToken(null);
            setSessionId(null);
            displayToast('Login Failed! No Csrf Token and session id', 'failure', 10000);
        }else{
            setIsLoggedIn(true);
            setCsrfToken(csrfToken);
            setSessionId(sessionId);
            displayToast('Login Success', 'success', 5000);
            window.location.replace("/ui/home");
        }
    }
}

function displayToast(message, type = 'success', duration = 10000){
    const toastContainer = document.getElementById('toastContainer');
    const toast = document.createElement('div');
    toast.id = `toast-${type}`;
    toast.textContent = message;
    toastContainer.appendChild(toast);
    setTimeout(() =>{
        toast.remove()
    }, duration);
}

function createInputElement(type, id, placeholder, required){
    const element = document.createElement("input");
    element.type = type;
    element.id = id;
    element.placeholder = placeholder;
    element.required = required;
    return element;
}

function createButtonElement(type, id, textContent){
    const element = document.createElement("button");
    element.type = type;
    element.id = id;
    element.textContent = textContent;
    return element;
}

function createFormElement(id){
    const element = document.createElement('form');
    element.id = id;
    return element;
}

function displayLoginForm(){
    const loginFormContainer = document.getElementById("loginFormContainer");
    const loginForm = document.getElementById('loginForm');
    if(loginForm){
        loginForm.remove();
    }else{
        const usernameElement = createInputElement("text", "username", "Username", true);
        const passwordElement = createInputElement("password", "password", "Password", true);
        const loginSubmitButtonElement = createButtonElement("submit", "loginSubmitButton", "Submit");
        const loginFormElement = createFormElement("loginForm");
        loginFormElement.appendChild(usernameElement);
        loginFormElement.appendChild(passwordElement);
        loginFormElement.appendChild(loginSubmitButtonElement);
        loginFormElement.addEventListener('submit', loginFormSubmitEventHandler);
        loginFormContainer.appendChild(loginFormElement);
    }
}