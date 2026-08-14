const API_BASE = (window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1") 
    ? window.location.origin 
    : "https://smart-token-backend-l8zm.onrender.com";
const WS_BASE = API_BASE.replace(/^http/, 'ws');

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

const aiChatTrigger = document.getElementById("ai-chat-trigger");
const aiChatWindow = document.getElementById("ai-chat-window");
const aiChatClose = document.getElementById("ai-chat-close");

let aiRecommendedService = null;

// Toggle Floating Chat Panel
aiChatTrigger.addEventListener("click", () => {
    if (aiChatWindow.style.display === "none" || !aiChatWindow.style.display) {
        aiChatWindow.style.display = "flex";
        aiInput.focus();
    } else {
        aiChatWindow.style.display = "none";
    }
});

aiChatClose.addEventListener("click", () => {
    aiChatWindow.style.display = "none";
});

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
        
        // Populate required documents list
        aiRecDocs.innerHTML = "";
        if (data.documents && data.documents.length > 0) {
            data.documents.forEach(doc => {
                const li = document.createElement("li");
                li.textContent = doc;
                aiRecDocs.appendChild(li);
            });
        } else {
            const li = document.createElement("li");
            li.textContent = "Standard ID & Address Proof";
            aiRecDocs.appendChild(li);
        }
        
        aiRecReason.textContent = data.reasoning;
        
        const centerNames = {
            BANK: "Bank Branch",
            ESEVAI: "E-Sevai Maiyam",
            POST_OFFICE: "Post Office",
            MUNICIPAL: "Municipal Corporation"
        };
        
        // Check if the service belongs to the current center
        if (data.belongs_to_current_center) {
            aiRecService.textContent = `${data.service_code} - ${data.service_name}`;
            aiGenerateBtn.textContent = "🎫 Generate Ticket";
            aiGenerateBtn.className = "btn btn-success";
            aiGenerateBtn.onclick = () => generateRecommendedTicket(sessionOffice);
        } else {
            const targetName = centerNames[data.recommended_center] || data.recommended_center;
            aiRecService.textContent = `[${targetName}] ${data.service_code} - ${data.service_name}`;
            
            aiGenerateBtn.textContent = `🎫 Generate Ticket & Transfer to ${targetName}`;
            aiGenerateBtn.className = "btn btn-primary";
            aiGenerateBtn.onclick = () => generateRecommendedTicket(data.recommended_center);
        }
        
        aiSuggestionBox.style.display = "flex";
    } catch (err) {
        console.error("AI Routing fallback:", err);
        aiRecommendedService = {
            service_code: "GEN",
            service_name: "General Help",
            belongs_to_current_center: true,
            recommended_center: sessionOffice,
            reasoning: "Please select your required service category from the main menu below to generate your queue ticket.",
            documents: ["Standard Government Photo ID (Aadhaar / Voter ID)"]
        };
        aiRecService.textContent = "General Kiosk Service";
        aiRecReason.textContent = aiRecommendedService.reasoning;
        aiRecDocs.innerHTML = "<li>Bring standard government photo ID (Aadhaar / Voter ID)</li>";
        aiGenerateBtn.textContent = "🎫 Generate Ticket";
        aiGenerateBtn.className = "btn btn-primary";
        aiGenerateBtn.onclick = () => { aiSuggestionBox.style.display = "none"; };
        aiSuggestionBox.style.display = "flex";
    } finally {
        aiAskBtn.disabled = false;
        aiAskBtn.textContent = "Ask";
    }
});

// Clear AI Box
aiCancelBtn.addEventListener("click", () => {
    aiInput.value = "";
    aiSuggestionBox.style.display = "none";
    aiRecommendedService = null;
});

// Generate AI Recommended Ticket & Cross-Kiosk Transfer
async function generateRecommendedTicket(overrideTargetOffice) {
    if (!aiRecommendedService) return;
    
    const targetOffice = overrideTargetOffice || aiRecommendedService.recommended_center || sessionOffice;
    const centerNames = {
        BANK: "Bank Branch",
        ESEVAI: "E-Sevai Maiyam",
        POST_OFFICE: "Post Office",
        MUNICIPAL: "Municipal Corporation"
    };
    const targetName = centerNames[targetOffice] || targetOffice;
    
    // Ask for mobile phone number for alerts if not entered
    let customerPhone = phoneInput.value.trim();
    if (!customerPhone) {
        customerPhone = prompt(`Please enter your 10-digit Mobile Number for queue ticket & Telegram alert at ${targetName}:`) || "";
    }
    
    if (!customerPhone || customerPhone.trim().length < 5) {
        alert("Mobile number is required to receive queue token alerts.");
        return;
    }
    
    aiGenerateBtn.disabled = true;
    aiGenerateBtn.textContent = "Generating Ticket...";
    const customerEmail = sessionStorage.getItem("userEmail");
    const customerInfo = customerPhone.trim();
    
    try {
        const response = await fetch(`${API_BASE}/api/tokens/generate?office_type=${targetOffice}`, {
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
        
        // Save the generated token to session to track across pages
        sessionStorage.setItem("activeCustomerToken", token.token_number);
        sessionStorage.setItem("activeCustomerOffice", targetOffice);
        sessionStorage.setItem("activeTokenService", token.service_name);
        
        // Hide AI Box
        aiInput.value = "";
        aiSuggestionBox.style.display = "none";
        aiChatWindow.style.display = "none";
        
        if (targetOffice !== sessionOffice) {
            sessionStorage.setItem("userOffice", targetOffice);
            alert(`✅ Token ${token.token_number} generated successfully!\nTransferring you to the ${targetName} kiosk.`);
            window.location.href = `/static/kiosk.html?center=${targetOffice}&token=${token.token_number}`;
        } else {
            // Show ticket success modal
            ticketNumber.textContent = token.token_number;
            ticketService.textContent = token.service_name;
            ticketTime.textContent = new Date(token.created_at).toLocaleString();
            
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
            
            successModal.style.display = "flex";
            checkAndLoadActiveToken();
        }
    } catch (err) {
        alert(err.message || "Error generating ticket.");
        console.error(err);
    } finally {
        aiGenerateBtn.disabled = false;
        aiGenerateBtn.textContent = "Generate Ticket";
    }
}

// Fetch AI predicted wait time
async function fetchAIWaitTime() {
    try {
        const response = await fetch(`${API_BASE}/api/admin/ai-insights?office_type=${sessionOffice}`);
        if (response.ok) {
            const data = await response.json();
            const waitTimeEl = document.getElementById("user-token-wait-time");
            if (data.predicted_wait_time_minutes > 0) {
                waitTimeEl.textContent = `~${data.predicted_wait_time_minutes} minutes`;
            } else {
                waitTimeEl.textContent = `Less than 5 minutes`;
            }
        }
    } catch (err) {
        console.error("Error loading AI wait time:", err);
    }
}

// Fetch user's active token and update UI
async function checkAndLoadActiveToken() {
    const container = document.getElementById("user-token-container");
    const email = sessionStorage.getItem("userEmail");
    
    // Check URL parameters & sessionStorage
    const urlParams = new URLSearchParams(window.location.search);
    const urlToken = urlParams.get("token");
    const activeTokenNum = sessionStorage.getItem("activeCustomerToken");
    const activeOffice = sessionStorage.getItem("activeCustomerOffice") || sessionOffice;
    
    const displayToken = urlToken || (activeOffice === sessionOffice ? activeTokenNum : null);
    
    if (displayToken) {
        container.style.display = "flex";
        document.getElementById("user-token-number").textContent = displayToken;
        const savedSvc = sessionStorage.getItem("activeTokenService") || "Queue Ticket";
        document.getElementById("user-token-service").textContent = savedSvc;
        
        const statusEl = document.getElementById("user-token-status");
        statusEl.textContent = "PENDING";
        statusEl.style.background = "rgba(99, 102, 241, 0.15)";
        statusEl.style.border = "1px solid rgba(99, 102, 241, 0.3)";
        statusEl.style.color = "var(--accent-primary)";
        
        document.getElementById("user-token-wait-time-container").style.display = "block";
        fetchAIWaitTime();
    }
    
    if (!email) return;
    
    try {
        const response = await fetch(`${API_BASE}/api/tokens/active?office_type=${sessionOffice}&email=${email}`);
        if (response.ok) {
            const token = await response.json();
            if (token) {
                sessionStorage.setItem("activeCustomerToken", token.token_number);
                sessionStorage.setItem("activeCustomerOffice", sessionOffice);
                sessionStorage.setItem("activeTokenService", token.service_name);
                
                container.style.display = "flex";
                document.getElementById("user-token-number").textContent = token.token_number;
                document.getElementById("user-token-service").textContent = token.service_name;
                
                const statusEl = document.getElementById("user-token-status");
                statusEl.textContent = token.status;
                
                if (token.status === "SERVING") {
                    statusEl.style.background = "rgba(16, 185, 129, 0.15)";
                    statusEl.style.border = "1px solid rgba(16, 185, 129, 0.3)";
                    statusEl.style.color = "var(--accent-success)";
                    document.getElementById("user-token-wait-time-container").style.display = "none";
                } else if (token.status === "HOLD") {
                    statusEl.style.background = "rgba(245, 158, 11, 0.15)";
                    statusEl.style.border = "1px solid rgba(245, 158, 11, 0.3)";
                    statusEl.style.color = "var(--accent-warning)";
                    document.getElementById("user-token-wait-time-container").style.display = "none";
                } else {
                    statusEl.style.background = "rgba(99, 102, 241, 0.15)";
                    statusEl.style.border = "1px solid rgba(99, 102, 241, 0.3)";
                    statusEl.style.color = "var(--accent-primary)";
                    document.getElementById("user-token-wait-time-container").style.display = "block";
                    fetchAIWaitTime();
                }
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
        
        let limitBadgeHtml = "";
        if (typeof getServiceConfig === "function") {
            const cfg = getServiceConfig(officeType, service.code);
            if (cfg) {
                limitBadgeHtml = `
                    <div style="margin-top: 0.6rem; font-size: 0.75rem; font-weight: 700; color: var(--accent-success); background: rgba(16, 185, 129, 0.12); padding: 0.3rem 0.6rem; border-radius: 12px; border: 1px solid rgba(16, 185, 129, 0.25); display: inline-block;">
                        🎫 Daily Cap: ${cfg.dailyLimit} tokens/day (${cfg.activeCounters} Counters @ ${cfg.avgServiceTimeMins}m)
                    </div>
                `;
            }
        }
        
        card.innerHTML = `
            <div class="card-icon">${service.icon}</div>
            <div class="card-title">${service.name}</div>
            <div class="card-desc">${service.desc}</div>
            ${limitBadgeHtml}
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
    
    const customerInfo = phoneInput.value.trim() || "6389082454";
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

// Auto-trigger search query from redirect
const urlParams = new URLSearchParams(window.location.search);
const autoQuery = urlParams.get("auto_query");
if (autoQuery) {
    aiChatWindow.style.display = "flex";
    aiInput.value = autoQuery;
    setTimeout(() => {
        aiAskBtn.click();
    }, 700);
}
