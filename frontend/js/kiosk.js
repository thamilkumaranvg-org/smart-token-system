const API_BASE = window.location.origin;
const WS_BASE = window.location.origin.replace(/^http/, 'ws');

// Verify Session
const sessionToken = sessionStorage.getItem("userToken");
const sessionRole = sessionStorage.getItem("userRole");
const sessionOffice = sessionStorage.getItem("userOffice") || "BANK";

if (!sessionToken || sessionRole !== "customer") {
    window.location.href = "/static/index.html";
}

// Request notification permissions
if ("Notification" in window) {
    console.log("Notifications API supported. Current permission:", Notification.permission);
    if (Notification.permission !== "granted" && Notification.permission !== "denied") {
        Notification.requestPermission().then(permission => {
            console.log("Notification permission requested. Result:", permission);
        });
    }
} else {
    console.warn("Notifications API is not supported by this browser.");
}

// Service mappings based on office type
const OFFICE_SERVICES = {
    BANK: [
        { code: "AC", name: "Account Opening & KYC", desc: "Open new account, submit documentations, update address", icon: "👤" },
        { code: "CS", name: "Cash Transactions", desc: "Deposit cash, withdraw money, process cheques", icon: "💵" },
        { code: "AD", name: "Aadhaar & Loans", desc: "Aadhaar update, loan applications, FD/RD setups", icon: "💼" }
    ],
    ESEVAI: [
        { code: "RV", name: "Revenue Certificates", desc: "Community, Income, Nativity, First Graduate certificates", icon: "📝" },
        { code: "SS", name: "Pension Schemes", desc: "Old Age Pension, Destitute Widow, Disability pension", icon: "👵" },
        { code: "LD", name: "Land & Utilities", desc: "Patta transfer, Chitta, A-Register, Electricity bills", icon: "🏠" }
    ],
    POST_OFFICE: [
        { code: "MP", name: "Mails & Parcels", desc: "Speed Post, Registered Post, domestic/international mail", icon: "📦" },
        { code: "SB", name: "Savings Bank & Money transfer", desc: "Post office savings account, IPPB, Money orders", icon: "🏦" },
        { code: "INS", name: "Postal Life Insurance", desc: "PLI, RPLI, Pradhan Mantri Bima Yojana applications", icon: "🛡️" },
        { code: "RT", name: "Retail & Aadhaar", desc: "Aadhaar services, Passport Seva Seva, stamps purchase", icon: "🛍️" }
    ],
    MUNICIPAL: [
        { code: "CR", name: "Civil Registration", desc: "Birth certificate, Death certificate, Marriage registration", icon: "👶" },
        { code: "TX", name: "Taxation & Payments", desc: "Property tax, professional tax payment, trade licensing dues", icon: "🪙" },
        { code: "PL", name: "Permits & Licenses", desc: "Building permissions, construction approvals, license renewal", icon: "🏗️" },
        { code: "UG", name: "Utilities & Grievances", desc: "Water connection request, drainage issues, municipal complaints", icon: "🛠️" }
    ]
};

let selectedService = null;

// DOM Elements
const officeTypeTag = document.getElementById("office-type-tag");
const servicesGrid = document.getElementById("services-grid");
const phoneModal = document.getElementById("phone-modal");
const successModal = document.getElementById("success-modal");
const phoneInput = document.getElementById("phone-input");

const modalServiceName = document.getElementById("modal-service-name");
const modalCancelBtn = document.getElementById("modal-cancel-btn");
const modalConfirmBtn = document.getElementById("modal-confirm-btn");

const ticketNumber = document.getElementById("ticket-number");
const ticketService = document.getElementById("ticket-service");
const ticketTime = document.getElementById("ticket-time");
const successCloseBtn = document.getElementById("success-close-btn");

const activeCalledDisplay = document.getElementById("active-called-display");
const customerLogoutBtn = document.getElementById("customer-logout-btn");

// Logout Action
customerLogoutBtn.addEventListener("click", () => {
    sessionStorage.clear();
    window.location.href = "/static/index.html";
});

// AI Assistant DOM Elements
const aiInput = document.getElementById("ai-input");
const aiAskBtn = document.getElementById("ai-ask-btn");
const aiSuggestionBox = document.getElementById("ai-suggestion-box");
const aiRecService = document.getElementById("ai-rec-service");
const aiRecReason = document.getElementById("ai-rec-reason");
const aiRecDocs = document.getElementById("ai-rec-docs");
const aiCancelBtn = document.getElementById("ai-cancel-btn");
const aiGenerateBtn = document.getElementById("ai-generate-btn");
const ticketDocsContainer = document.getElementById("ticket-docs-container");
const ticketDocsList = document.getElementById("ticket-docs-list");

let aiRecommendedService = null;

// Ask AI Event Handler
aiAskBtn.addEventListener("click", async () => {
    const query = aiInput.value.trim();
    if (!query) {
        alert("Please describe what you want to do first.");
        return;
    }
    
    aiAskBtn.disabled = true;
    aiAskBtn.textContent = "Thinking...";
    
    try {
        const response = await fetch(`${API_BASE}/api/ai/route-service`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                user_input: query,
                office_type: sessionOffice
            })
        });
        
        if (!response.ok) {
            const errData = await response.json();
            throw new Error(errData.detail || "AI failed to route service.");
        }
        
        const data = await response.json();
        
        aiRecommendedService = data;
        
        // Show recommended service
        aiRecService.textContent = `${data.service_code} - ${data.service_name}`;
        aiRecReason.textContent = data.reasoning;
        
        // Populate documents list
        aiRecDocs.innerHTML = "";
        if (data.documents && data.documents.length > 0) {
            data.documents.forEach(doc => {
                const li = document.createElement("li");
                li.textContent = doc;
                aiRecDocs.appendChild(li);
            });
        } else {
            const li = document.createElement("li");
            li.textContent = "None specified. Bring standard ID proof.";
            aiRecDocs.appendChild(li);
        }
        
        aiSuggestionBox.style.display = "flex";
    } catch (err) {
        alert(err.message || "Error calling Gemini AI. Make sure GEMINI_API_KEY is configured.");
        console.error(err);
    } finally {
        aiAskBtn.disabled = false;
        aiAskBtn.textContent = "Ask AI";
    }
});

// Clear AI Box
aiCancelBtn.addEventListener("click", () => {
    aiInput.value = "";
    aiSuggestionBox.style.display = "none";
    aiRecommendedService = null;
});

// Generate AI Recommended Ticket
aiGenerateBtn.addEventListener("click", async () => {
    if (!aiRecommendedService) return;
    
    aiGenerateBtn.disabled = true;
    const customerEmail = sessionStorage.getItem("userEmail");
    
    // Convert documents to single string for customer_info
    const docsStr = aiRecommendedService.documents ? aiRecommendedService.documents.join(", ") : "";
    const customerInfo = docsStr ? `Required Docs: ${docsStr}` : "AI Routed Ticket";
    
    try {
        const response = await fetch(`${API_BASE}/api/tokens/generate?office_type=${sessionOffice}`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                service_code: aiRecommendedService.service_code,
                service_name: aiRecommendedService.service_name,
                customer_info: customerInfo,
                customer_email: customerEmail || null
            })
        });
        
        if (!response.ok) {
            const errData = await response.json();
            throw new Error(errData.detail || "Failed to generate token");
        }
        
        const token = await response.json();
        
        // Save the generated token to session to track for targeted notifications
        sessionStorage.setItem("activeCustomerToken", token.token_number);
        
        // Hide AI Box
        aiInput.value = "";
        aiSuggestionBox.style.display = "none";
        
        // Show ticket success modal with documents
        ticketNumber.textContent = token.token_number;
        ticketService.textContent = token.service_name;
        
        const dateStr = new Date(token.created_at).toLocaleString();
        ticketTime.textContent = dateStr;
        
        // Show required documents list in success modal
        ticketDocsList.innerHTML = "";
        if (aiRecommendedService.documents && aiRecommendedService.documents.length > 0) {
            aiRecommendedService.documents.forEach(doc => {
                const li = document.createElement("li");
                li.textContent = doc;
                ticketDocsList.appendChild(li);
            });
            ticketDocsContainer.style.display = "block";
        } else {
            ticketDocsContainer.style.display = "none";
        }
        
        successModal.classList.add("active");
        
        // Refresh active token display
        checkAndLoadActiveToken();
        
    } catch (err) {
        alert(err.message || "Error generating token.");
        console.error(err);
    } finally {
        aiGenerateBtn.disabled = false;
        aiRecommendedService = null;
    }
});

// Fetch user's active token and update UI
async function checkAndLoadActiveToken() {
    const email = sessionStorage.getItem("userEmail");
    if (!email) return;
    
    try {
        const response = await fetch(`${API_BASE}/api/tokens/active?office_type=${sessionOffice}&email=${email}`);
        if (response.ok) {
            const token = await response.json();
            const container = document.getElementById("user-token-container");
            if (token) {
                // Save the generated token to session to track for notifications
                sessionStorage.setItem("activeCustomerToken", token.token_number);
                
                // Show container and populate
                container.style.display = "flex";
                document.getElementById("user-token-number").textContent = token.token_number;
                document.getElementById("user-token-service").textContent = token.service_name;
                
                const statusEl = document.getElementById("user-token-status");
                statusEl.textContent = token.status;
                
                // Style based on status
                if (token.status === "SERVING") {
                    statusEl.style.background = "rgba(16, 185, 129, 0.15)";
                    statusEl.style.border = "1px solid rgba(16, 185, 129, 0.3)";
                    statusEl.style.color = "var(--accent-success)";
                } else if (token.status === "HOLD") {
                    statusEl.style.background = "rgba(245, 158, 11, 0.15)";
                    statusEl.style.border = "1px solid rgba(245, 158, 11, 0.3)";
                    statusEl.style.color = "var(--accent-warning)";
                } else {
                    // PENDING
                    statusEl.style.background = "rgba(99, 102, 241, 0.15)";
                    statusEl.style.border = "1px solid rgba(99, 102, 241, 0.3)";
                    statusEl.style.color = "var(--accent-primary)";
                }
            } else {
                sessionStorage.removeItem("activeCustomerToken");
                container.style.display = "none";
            }
        }
    } catch (err) {
        console.error("Error loading user active token:", err);
    }
}

// Initialize Kiosk
async function initKiosk() {
    officeTypeTag.textContent = sessionOffice.replace("_", " ");
    renderServices(sessionOffice);
    loadActiveServingToken();
    checkAndLoadActiveToken();
}

// Render service cards based on office type
function renderServices(officeType) {
    const services = OFFICE_SERVICES[officeType] || OFFICE_SERVICES.BANK;
    servicesGrid.innerHTML = "";
    
    services.forEach(service => {
        const card = document.createElement("div");
        card.className = "menu-card glass-container";
        card.innerHTML = `
            <div class="card-icon">${service.icon}</div>
            <div class="card-title">${service.name}</div>
            <div class="card-desc">${service.desc}</div>
        `;
        card.addEventListener("click", () => openPhoneModal(service));
        servicesGrid.appendChild(card);
    });
}

// Fetch and display active called token
async function loadActiveServingToken() {
    try {
        const response = await fetch(`${API_BASE}/api/queues/status?office_type=${sessionOffice}`);
        const status = await response.json();
        
        if (status.active_tokens && status.active_tokens.length > 0) {
            const lastCalled = status.active_tokens[status.active_tokens.length - 1];
            activeCalledDisplay.textContent = `${lastCalled.token_number} at Counter ${lastCalled.counter_assigned}`;
        } else {
            activeCalledDisplay.textContent = "None (Lobby Quiet)";
        }
    } catch (err) {
        console.error("Error fetching active serving status:", err);
    }
}

// Open Phone entry Modal
function openPhoneModal(service) {
    selectedService = service;
    modalServiceName.textContent = service.name;
    phoneInput.value = "";
    phoneModal.classList.add("active");
}

// Close Phone Modal
modalCancelBtn.addEventListener("click", () => {
    phoneModal.classList.remove("active");
    selectedService = null;
});

// Generate Token
modalConfirmBtn.addEventListener("click", async () => {
    if (!selectedService) return;
    
    const customerInfo = phoneInput.value.trim();
    const customerEmail = sessionStorage.getItem("userEmail");
    modalConfirmBtn.disabled = true;
    
    try {
        const response = await fetch(`${API_BASE}/api/tokens/generate?office_type=${sessionOffice}`, {
            method: "POST",
            headers: {
                "Content-Type": "application/json"
            },
            body: JSON.stringify({
                service_code: selectedService.code,
                service_name: selectedService.name,
                customer_info: customerInfo || null,
                customer_email: customerEmail || null
            })
        });
        
        if (!response.ok) {
            const errData = await response.json();
            throw new Error(errData.detail || "Failed to generate token");
        }
        
        const token = await response.json();
        
        // Save the generated token to session to track for targeted notifications
        sessionStorage.setItem("activeCustomerToken", token.token_number);
        console.log("Saved active customer token to session storage:", token.token_number);
        
        // Hide phone modal
        phoneModal.classList.remove("active");
        
        // Show ticket success modal
        ticketNumber.textContent = token.token_number;
        ticketService.textContent = token.service_name;
        
        const dateStr = new Date(token.created_at).toLocaleString();
        ticketTime.textContent = dateStr;
        
        // Hide documents container for manual generations
        ticketDocsContainer.style.display = "none";
        
        successModal.classList.add("active");
        
        // Refresh our active token display
        checkAndLoadActiveToken();
        
    } catch (err) {
        alert(err.message || "Error generating token. Please check backend server.");
        console.error(err);
    } finally {
        modalConfirmBtn.disabled = false;
    }
});

// Close Success Modal
successCloseBtn.addEventListener("click", () => {
    successModal.classList.remove("active");
});

// Setup WebSocket Listener
function setupWebSocket() {
    const socket = new WebSocket(`${WS_BASE}/ws/queue`);
    
    socket.onmessage = (event) => {
        const msg = JSON.parse(event.data);
        console.log("WebSocket event received on Kiosk:", msg);
        
        // Filter by office type
        if (msg.office_type && msg.office_type !== sessionOffice) {
            return;
        }
        
        if (msg.type === "CALL_TOKEN") {
            loadActiveServingToken();
            checkAndLoadActiveToken();
            
            const myToken = sessionStorage.getItem("activeCustomerToken");
            const calledToken = msg.data;
            
            console.log("Comparing called token", calledToken.token_number, "with my saved token", myToken);
            
            if (myToken && calledToken.token_number === myToken) {
                console.log("Targeted token match! Attempting web notification. Status:", Notification.permission);
                if ("Notification" in window) {
                    if (Notification.permission === "granted") {
                        try {
                            const notification = new Notification("🔔 Your Token Has Been Called!", {
                                body: `Token ${calledToken.token_number}, please proceed immediately to Counter ${calledToken.counter_assigned}.`,
                                requireInteraction: true
                            });
                            console.log("Notification object successfully created:", notification);
                        } catch (err) {
                            console.error("Failed to build notification card:", err);
                        }
                    } else {
                        console.warn("Cannot show notification: permission is", Notification.permission);
                    }
                }
            }
        } else if (msg.type === "UPDATE_STATUS" || msg.type === "NEW_TOKEN") {
            loadActiveServingToken();
            checkAndLoadActiveToken();
        }
    };
    
    socket.onclose = () => {
        setTimeout(setupWebSocket, 3000);
    };
}

// Start application
initKiosk();
setupWebSocket();
