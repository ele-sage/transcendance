import { confirmLogin } from "./auth";
import * as auth from "/static/js/auth.js";

// -- fetch ----
function fetchRoute({
        route,
        options=null,
        responseManager=fetchResponse,
        dataManager=(_) => {},
        errorManager=fetchError,
        requireAuthorized=true,
    }){
    fetch(route, options)
    .then(responseManager)
    .then(dataManager)
    .catch(error => {
        if (requireAuthorized && !isAuthorized(error)) {
            return;
        }
        errorManager(error);
    });
}

function fetchResponse(response) {
    if (response.ok) {
        return response.json();
    } else {
        return response.json().then(errorData => {
            throw { status: response.status, data: errorData };
        });
    }        
}

function isAuthorized(error) {
    switch (error.status) {
        case 401:
            fetchRoute({
                route: "/api/refresh/",
                options: { method: "POST" },
            });
            break;
        case 403:
            auth.reConnect();
            break;
        default:
            return true;
    }
    return false;
}

function fetchError(error) {
    if (error.stack) { //// TODO: check if works
        console.error(error.stack);
        return;
    }
    console.log(`HTTP error! Status: ${error.status}`);
    if (error.data) {
        console.log(`Error Data: ${error.data}\n`);
    }
}
// --

// -- form ----
function formSubmit(formId, callback, method=undefined) {
    const form = document.getElementById(formId);
    if (!form) {
        console.error('Form "' + formId + '" not found');
        return;
    }    
    removeFormErrors();
    method = method ? method : form.method;
    const options = {
        method: method,
        body: new FormData(form),
    };
    const dataManager = (data) => {
        callback(data);
        clearForm(formId);
    };
    const errorManager = (error) => {
        console.log("error.status:", error.status);
        console.log("error.data:", error.data);
        if (error.status && error.data) {
            for (const [key, value] of Object.entries(error.data)) {
                addFormError(form, key, value);
            }
            return;
        }
        fetchError(error);
    };
    fetchRoute({
        route: form.action,
        options: options,
        dataManager: dataManager,
        errorManager: errorManager
    })
}

function addFormError(form, key, value) {
    const div = form.querySelector("." + key);
    if (!div) {
        return;
    }
    const error = document.createElement('p');
    error.className = "form-error";
    error.innerText = value;
    div.appendChild(error);
}

function removeFormErrors() {
    let errors = document.querySelectorAll(".form-error");
    errors.forEach((error) => {
        error.outerHTML = "";
    });
}

function clearForm(formId) {
    const form = document.getElementById(formId);
    const inputFields = form.querySelectorAll('input');
    inputFields.forEach(input => {
        if (input.value) {
            input.value = '';
        }
    });
}
// --


export { formSubmit, fetchRoute };