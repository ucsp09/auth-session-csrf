main();

function main(){
    addEventHandlers();
}

function addEventHandlers(){
    const performCSRFAttackWithNoCSRFTokenButton = document.getElementById('performCSRFAttackWithNoCSRFTokenButton');
    performCSRFAttackWithNoCSRFTokenButton.addEventListener('click', performCSRFAttackWithNoCSRFTokenButtonClickEventHandler);
    const performCSRFAttackWithFakeCSRFTokenButton = document.getElementById('performCSRFAttackWithFakeCSRFTokenButton');
    performCSRFAttackWithFakeCSRFTokenButton.addEventListener('click', performCSRFAttackWithFakeCSRFTokenButtonClickEventHandler);
}

async function performCSRFAttackWithNoCSRFTokenButtonClickEventHandler(){
    const response =  await callGetAllProtectedResourcesAPI();
    if(response.status === 200){
        const data = await response.json();
        console.log("Protected Resources Data:", data);
        showToast("CSRF Attack Successful! Protected resources accessed.", 5000);
    } else {
        console.error("Failed to access protected resources. Status:", response.status);
        showToast("CSRF Attack Failed! Could not access protected resources.", 5000);
    }
}

async function performCSRFAttackWithFakeCSRFTokenButtonClickEventHandler(){
    const response =  await callGetAllProtectedResourcesAPIWithFakeCSRFToken();
    if(response.status === 200){
        const data = await response.json();
        console.log("Protected Resources Data:", data);
        showToast("CSRF Attack with Fake CSRF Token Successful! Protected resources accessed.", 5000);
    } else {
        console.error("Failed to access protected resources. Status:", response.status);
        showToast("CSRF Attack with Fake CSRF Token Failed! Could not access protected resources.", 5000);
    }
}

async function callGetAllProtectedResourcesAPIWithFakeCSRFToken(){
    const url = "http://localhost:3000/ui/protected/resources";
    const fakeCSRFToken = "fake-csrf-token-12345";
    const response = await fetch(url, {
        method: 'GET',
        headers: {
            'X-CSRF-Token': fakeCSRFToken
        },
        credentials: 'include'
    });
    return response;
}

async function callGetAllProtectedResourcesAPI(){
    const url = "http://localhost:3000/ui/protected/resources";
    const response = await fetch(url, {
        method: 'GET',
        credentials: 'include'
    });
    return response;
}

function showToast(message, duration=3000){
    const toastContainer = document.getElementById('toast-container');

    const toast = document.createElement('div');
    toast.className = 'toast';
    toast.textContent = message;

    toastContainer.appendChild(toast);

    setTimeout(() => {
        toastContainer.removeChild(toast);
    }, duration);
}