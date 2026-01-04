
main();

function main(){
    displayNavBar();
}

function createDivElement(className){
    const element = document.createElement("div");
    element.className = className;
    return element
}

function createAnchorElement(id, href, textContent){
    const element = document.createElement('a');
    element.id = id;
    element.href = href;
    element.textContent = textContent;
    return element;
}

function createButtonElement(id, type, textContent){
    const element = document.createElement('button');
    element.id = id;
    element.type = type;
    element.textContent = textContent;
    return element;
}

function displayNavBar(){
    const navbarContainer = document.getElementById('navbarContainer');
    
    const homePageNavBarItem = createDivElement("navBarItem");
    const homePageAnchorElement = createAnchorElement('homePage', '/ui/home', 'Home');
    homePageNavBarItem.appendChild(homePageAnchorElement);
    
    const logoutButtonNavBarItem = createDivElement("navBarItem");
    const logoutButtonElement = createButtonElement('logoutButton', 'button', 'Logout');
    logoutButtonNavBarItem.appendChild(logoutButtonElement);

    navbarContainer.appendChild(homePageNavBarItem);
    navbarContainer.appendChild(logoutButtonNavBarItem);
}