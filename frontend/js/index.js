const selector = document.getElementById("hub-office-selector");
const proceedBtn = document.getElementById("proceed-btn");

function chooseCenter(officeCode) {
    if (selector) selector.value = officeCode;
    window.location.href = `/static/login.html?center=${officeCode}`;
}

if (proceedBtn) {
    proceedBtn.addEventListener("click", () => {
        const selectedOffice = selector.value;
        window.location.href = `/static/login.html?center=${selectedOffice}`;
    });
}
