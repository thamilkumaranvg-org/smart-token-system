// Global Multi-Language System (100% Pure English or 100% Pure Tamil Persistence)
const TRANSLATIONS = {
    en: {
        // App Header & Branding
        appTitle: "Smart Token System",
        authPortal: "Authentication Portal",
        agentConsole: "Counter Agent Console",
        adminDashboard: "Office Admin Dashboard",
        lobbyDisplay: "Lobby Display Panel",
        govBrand: "Tamil Nadu Government Services",
        
        // Navigation & Actions
        signIn: "Sign In",
        register: "Register Account",
        logout: "Logout",
        selectCenter: "Select Public Center",
        changeLang: "Change Language",
        switchLang: "🌐 Switch Language",
        selectCenterBtn: "Select Center →",
        
        // Login Page
        signInTitle: "Sign In",
        signInSubtitle: "Sign in with your registered credentials to access your console.",
        emailLabel: "Email Address",
        passwordLabel: "Password",
        confirmPasswordLabel: "Confirm Password",
        newVisitor: "New visitor?",
        registerLink: "Register account",
        alreadyAccount: "Already have an account?",
        signupTitle: "Customer Registration",
        signupSubtitle: "Create a customer account to generate kiosk tickets and monitor live status.",
        registerBtn: "Register & Open Kiosk",
        
        // Agent Console
        counterLogin: "Counter Login",
        selectCounter: "Select Counter Number",
        startServing: "Start Serving",
        activeCustomer: "Active Customer",
        callNext: "Call Next Customer",
        recall: "Recall",
        recalled: "Recalled!",
        complete: "Mark Complete",
        missed: "Missed / No Show",
        lobbyQueue: "Lobby Queue Status",
        peopleWaiting: "People Waiting:",
        phone: "Phone:",
        
        // Admin Dashboard & Table Headers
        dailyPerformance: "Daily Performance Metrics",
        totalTokens: "Total Tokens Generated",
        currentlyServed: "Currently Served",
        pendingQueue: "Pending in Queue",
        noShowsMissed: "No-Shows / Missed",
        avgWaitTime: "Avg. Wait Time",
        aiOptimization: "AI Optimization Insights",
        predictedWaitTime: "PREDICTED WAIT TIME",
        lobbyEfficiency: "LOBBY EFFICIENCY RATING",
        queueBottleneck: "CURRENT QUEUE BOTTLENECK",
        aiRecommendation: "AI RECOMMENDATION",
        activeQueueDetails: "Active Queue Details",
        tokenNo: "TOKEN NO.",
        serviceCategory: "SERVICE CATEGORY",
        customerInfo: "CUSTOMER INFO",
        assignedCounter: "ASSIGNED COUNTER",
        createdAt: "CREATED AT",
        counterAllocation: "Counter Allocation",
        counterNo: "COUNTER NO.",
        currentAction: "CURRENT ACTION",
        addCounter: "+ Add Counter",
        enable: "Enable",
        disable: "Disable",
        
        // Kiosk Dashboard
        selfKiosk: "Self Service Kiosk",
        selectCategoryTitle: "Select Service Category",
        selectCategoryDesc: "Please select a category below to generate your queue ticket.",
        yourToken: "Your Active Token",
        statusLabel: "Status",
        estimatedWait: "Estimated Wait Time",
        activeCalled: "Active Called Token:",
        noneLobbyQuiet: "None (Lobby Quiet)",
        aiWaitTime: "🤖 AI Est. Wait Time:",
        askAiTitle: "AI Kiosk Assistant",
        askAiDesc: "Tell the AI what you need to do, and it will recommend the correct counter and required documents!",
        generateTicket: "Generate Ticket",
        mobileLabel: "Mobile Number (WhatsApp/Telegram)",
        mobilePlaceholder: "e.g., 9876543210",
        
        // Bank Service Titles & Descriptions
        AC: "Account Opening & KYC",
        AC_desc: "Open new account, submit documentations, update address",
        "Account Opening & KYC": "Account Opening & KYC",
        "Open new account, submit documentations, update address": "Open new account, submit documentations, update address",
        
        CS: "Cash Transactions",
        CS_desc: "Deposit cash, withdraw money, process cheques",
        "Cash Transactions": "Cash Transactions",
        "Deposit cash, withdraw money, process cheques": "Deposit cash, withdraw money, process cheques",
        
        AD: "Aadhaar & Loans",
        AD_desc: "Aadhaar update, loan applications, FD/RD setups",
        "Aadhaar & Loans": "Aadhaar & Loans",
        "Aadhaar update, loan applications, FD/RD setups": "Aadhaar update, loan applications, FD/RD setups",
        
        // E-Sevai Service Titles & Descriptions
        RV: "Revenue Certificates",
        RV_desc: "Community, Income, Nativity, First Graduate certificates",
        "Revenue Certificates": "Revenue Certificates",
        "Community, Income, Nativity, First Graduate certificates": "Community, Income, Nativity, First Graduate certificates",
        
        SS: "Pension Schemes",
        SS_desc: "Old Age Pension, Destitute Widow, Disability pension",
        "Pension Schemes": "Pension Schemes",
        "Old Age Pension, Destitute Widow, Disability pension": "Old Age Pension, Destitute Widow, Disability pension",
        
        LD: "Land & Utilities",
        LD_desc: "Patta transfer, Chitta, A-Register, Electricity bills",
        "Land & Utilities": "Land & Utilities",
        "Patta transfer, Chitta, A-Register, Electricity bills": "Patta transfer, Chitta, A-Register, Electricity bills",
        
        // Post Office Service Titles & Descriptions
        MP: "Mails & Parcels",
        MP_desc: "Speed Post, Registered Post, domestic/international mail",
        "Mails & Parcels": "Mails & Parcels",
        "Speed Post, Registered Post, domestic/international mail": "Speed Post, Registered Post, domestic/international mail",
        
        SB: "Savings Bank & Money transfer",
        SB_desc: "Post office savings account, IPPB, Money orders",
        "Savings Bank & Money transfer": "Savings Bank & Money transfer",
        "Post office savings account, IPPB, Money orders": "Post office savings account, IPPB, Money orders",
        
        INS: "Postal Life Insurance",
        INS_desc: "PLI, RPLI, Pradhan Mantri Bima Yojana applications",
        "Postal Life Insurance": "Postal Life Insurance",
        "PLI, RPLI, Pradhan Mantri Bima Yojana applications": "PLI, RPLI, Pradhan Mantri Bima Yojana applications",
        
        RT: "Retail & Aadhaar",
        RT_desc: "Aadhaar services, Passport Seva, stamps purchase",
        "Retail & Aadhaar": "Retail & Aadhaar",
        "Aadhaar services, Passport Seva, stamps purchase": "Aadhaar services, Passport Seva, stamps purchase",
        "Aadhaar services, Passport Seva Seva, stamps purchase": "Aadhaar services, Passport Seva, stamps purchase",
        
        // Municipal Service Titles & Descriptions
        CR: "Civil Registration",
        CR_desc: "Birth certificate, Death certificate, Marriage registration",
        "Civil Registration": "Civil Registration",
        "Birth certificate, Death certificate, Marriage registration": "Birth certificate, Death certificate, Marriage registration",
        
        TX: "Taxation & Payments",
        TX_desc: "Property tax, professional tax payment, trade licensing dues",
        "Taxation & Payments": "Taxation & Payments",
        "Property tax, professional tax payment, trade licensing dues": "Property tax, professional tax payment, trade licensing dues",
        
        PL: "Permits & Licenses",
        PL_desc: "Building permissions, construction approvals, license renewal",
        "Permits & Licenses": "Permits & Licenses",
        "Building permissions, construction approvals, license renewal": "Building permissions, construction approvals, license renewal",
        
        UG: "Utilities & Grievances",
        UG_desc: "Water connection request, drainage issues, municipal complaints",
        "Utilities & Grievances": "Utilities & Grievances",
        "Water connection request, drainage issues, municipal complaints": "Water connection request, drainage issues, municipal complaints",
        
        // Counter Names
        "Counter 1": "Counter 1",
        "Counter 2": "Counter 2",
        "Counter 3": "Counter 3",
        "Counter 4": "Counter 4",
        "Counter 5": "Counter 5"
    },
    ta: {
        // App Header & Branding
        appTitle: "ஸ்மார்ட் டோக்கன் முறைமை",
        authPortal: "அனுமதி நுழைவாயில்",
        agentConsole: "சேவை மேசை முகவர் பலகம்",
        adminDashboard: "நிர்வாகி தரவுப்பலகை",
        lobbyDisplay: "வரவேற்பறை காட்சித்திரை",
        govBrand: "தமிழ்நாடு அரசு சேவைகள்",
        
        // Navigation & Actions
        signIn: "உள்நுழை",
        register: "பதிவு செய்க",
        logout: "வெளியேறு",
        selectCenter: "பொது சேவை மையத்தைத் தேர்ந்தெடுக்கவும்",
        changeLang: "மொழி மாற்றம்",
        switchLang: "🌐 மொழி மாற்றம்",
        selectCenterBtn: "தேர்ந்தெடு →",
        
        // Login Page
        signInTitle: "உள்நுழைவு",
        signInSubtitle: "உங்கள் பதிவு செய்யப்பட்ட விவரங்களைப் பயன்படுத்தி உள்நுழையவும்.",
        emailLabel: "மின்னஞ்சல் முகவரி",
        passwordLabel: "கடவுச்சொல்",
        confirmPasswordLabel: "கடவுச்சொல்லை உறுதிப்படுத்தவும்",
        newVisitor: "புதிய பயனாளி?",
        registerLink: "கணக்கை பதிவு செய்க",
        alreadyAccount: "ஏற்கனவே கணக்கு உள்ளதா?",
        signupTitle: "பயனாளி பதிவு",
        signupSubtitle: "டோக்கன் பெற மற்றும் நிலையை அறிய புதிய கணக்கை உருவாக்கவும்.",
        registerBtn: "பதிவு செய்து டோக்கன் பெறுக",
        
        // Agent Console
        counterLogin: "சேவை மேசை உள்நுழைவு",
        selectCounter: "சேவை மேசை எண்ணைத் தேர்ந்தெடுக்கவும்",
        startServing: "சேவையைத் தொடங்கவும்",
        activeCustomer: "தற்போதைய பயனாளி",
        callNext: "அடுத்த பயனாளியை அழைக்கவும்",
        recall: "மீண்டும் அழைக்கவும்",
        recalled: "மீண்டும் அழைக்கப்பட்டது!",
        complete: "சேவை முடிந்தது",
        missed: "வரவில்லை / ரத்து செய்யப்பட்டது",
        lobbyQueue: "காத்திருப்போர் வரிசை நிலை",
        peopleWaiting: "காத்திருக்கும் நபர்கள்:",
        phone: "கைபேசி:",
        
        // Admin Dashboard & Table Headers
        dailyPerformance: "தினசரி செயல்திறன் அளவீடுகள்",
        totalTokens: "மொத்த டோக்கன்கள்",
        currentlyServed: "தற்போது வழங்கப்பட்டவை",
        pendingQueue: "வரிசையில் காத்திருப்பவை",
        noShowsMissed: "வரவில்லை / விடுபட்டவை",
        avgWaitTime: "சராசரி காத்திருப்பு நேரம்",
        aiOptimization: "AI மேலாண்மை வழிகாட்டல்",
        predictedWaitTime: "கணிக்கப்பட்ட காத்திருப்பு",
        lobbyEfficiency: "வரவேற்பறை திறன் மதிப்பீடு",
        queueBottleneck: "தற்போதைய தாமதம்",
        aiRecommendation: "AI பரிந்துரை",
        activeQueueDetails: "நடப்பு வரிசை விவரங்கள்",
        tokenNo: "டோக்கன் எண்",
        serviceCategory: "சேவை பிரிவு",
        customerInfo: "பயனாளி விவரம்",
        assignedCounter: "சேவை மேசை",
        createdAt: "உருவாக்கப்பட்ட நேரம்",
        counterAllocation: "சேவை மேசை ஒதுக்கீடு",
        counterNo: "சேவை மேசை எண்",
        currentAction: "நடப்பு நடவடிக்கை",
        addCounter: "+ மேசை சேர்க்க",
        enable: "இயக்கு",
        disable: "முடக்கு",
        
        // Kiosk Dashboard
        selfKiosk: "சுய சேவை டோக்கன் மையம்",
        selectCategoryTitle: "சேவை பிரிவைத் தேர்ந்தெடுக்கவும்",
        selectCategoryDesc: "டோக்கன் பெற கீழே உள்ள சேவை பிரிவைத் தேர்ந்தெடுக்கவும்.",
        yourToken: "உங்கள் நடப்பு டோக்கன்",
        statusLabel: "நிலை",
        estimatedWait: "எதிர்பார்க்கப்படும் காத்திருப்பு நேரம்",
        activeCalled: "தற்போது அழைக்கப்படும் டோக்கன்:",
        noneLobbyQuiet: "யாருமில்லை (அமைதியானது)",
        aiWaitTime: "🤖 AI கணித்த காத்திருப்பு நேரம்:",
        askAiTitle: "செயற்கை நுண்ணறிவு உதவியாளர்",
        askAiDesc: "உங்கள் தேவையை கூறினால் சரியான சேவை மேசையையும் தேவையான ஆவணங்களையும் AI பரிந்துரைக்கும்!",
        generateTicket: "டோக்கன் பெறுக",
        mobileLabel: "கைபேசி எண் (வாட்ஸ்அப்/டெலிகிராம்)",
        mobilePlaceholder: "எ.கா. 9876543210",
        
        // Bank Service Titles & Descriptions (Pure Tamil)
        AC: "கணக்கு துவக்கம் & KYC",
        AC_desc: "புதிய கணக்கு துவங்குதல், ஆவணங்கள் சமர்ப்பித்தல், முகவரி மாற்றம்",
        "Account Opening & KYC": "கணக்கு துவக்கம் & KYC",
        "Open new account, submit documentations, update address": "புதிய கணக்கு துவங்குதல், ஆவணங்கள் சமர்ப்பித்தல், முகவரி மாற்றம்",
        
        CS: "பணப் பரிவர்த்தனைகள்",
        CS_desc: "பணம் செலுத்துதல், பணம் எடுத்தல், காசோலை செயலாக்கம்",
        "Cash Transactions": "பணப் பரிவர்த்தனைகள்",
        "Deposit cash, withdraw money, process cheques": "பணம் செலுத்துதல், பணம் எடுத்தல், காசோலை செயலாக்கம்",
        
        AD: "ஆதார் & கடன்கள்",
        AD_desc: "ஆதார் புதுப்பித்தல், கடன் விண்ணப்பங்கள், நிலையான வைப்பு",
        "Aadhaar & Loans": "ஆதார் & கடன்கள்",
        "Aadhaar update, loan applications, FD/RD setups": "ஆதார் புதுப்பித்தல், கடன் விண்ணப்பங்கள், நிலையான வைப்பு",
        
        // E-Sevai Service Titles & Descriptions (Pure Tamil)
        RV: "வருவாய் சான்றிதழ்கள்",
        RV_desc: "சாதி, வருமானம், இருப்பிடம், முதல் பட்டதாரி சான்றிதழ்கள்",
        "Revenue Certificates": "வருவாய் சான்றிதழ்கள்",
        "Community, Income, Nativity, First Graduate certificates": "சாதி, வருமானம், இருப்பிடம், முதல் பட்டதாரி சான்றிதழ்கள்",
        
        SS: "ஓய்வூதிய திட்டங்கள்",
        SS_desc: "முதியோர் ஓய்வூதியம், விதவை ஓய்வூதியம், மாற்றுத்திறனாளி ஓய்வூதியம்",
        "Pension Schemes": "ஓய்வூதிய திட்டங்கள்",
        "Old Age Pension, Destitute Widow, Disability pension": "முதியோர் ஓய்வூதியம், விதவை ஓய்வூதியம், மாற்றுத்திறனாளி ஓய்வூதியம்",
        
        LD: "நிலம் & பயன்பாடுகள்",
        LD_desc: "பட்டா மாறுதல், சிட்டா, அ-பதிவேடு, மின்சார கட்டணம்",
        "Land & Utilities": "நிலம் & பயன்பாடுகள்",
        "Patta transfer, Chitta, A-Register, Electricity bills": "பட்டா மாறுதல், சிட்டா, அ-பதிவேடு, மின்சார கட்டணம்",
        
        // Post Office Service Titles & Descriptions (Pure Tamil)
        MP: "தபால் & பார்சல்கள்",
        MP_desc: "விரைவு தபால், பதிவு தபால், உள்நாட்டு மற்றும் சர்வதேச பார்சல்",
        "Mails & Parcels": "தபால் & பார்சல்கள்",
        "Speed Post, Registered Post, domestic/international mail": "விரைவு தபால், பதிவு தபால், உள்நாட்டு மற்றும் சர்வதேச பார்சல்",
        
        SB: "சேமிப்பு வங்கி & பணப் பரிமாற்றம்",
        SB_desc: "தபால் நிலைய சேமிப்பு கணக்கு, IPPB, மணி ஆர்டர்",
        "Savings Bank & Money transfer": "சேமிப்பு வங்கி & பணப் பரிமாற்றம்",
        "Post office savings account, IPPB, Money orders": "தபால் நிலைய சேமிப்பு கணக்கு, IPPB, மணி ஆர்டர்",
        
        INS: "தபால் ஆயுள் காப்பீடு",
        INS_desc: "PLI, RPLI, பிரதான் மந்திரி பீமா யோஜனா விண்ணப்பங்கள்",
        "Postal Life Insurance": "தபால் ஆயுள் காப்பீடு",
        "PLI, RPLI, Pradhan Mantri Bima Yojana applications": "PLI, RPLI, பிரதான் மந்திரி பீமா யோஜனா விண்ணப்பங்கள்",
        
        RT: "சில்லறை & ஆதார் சேவைகள்",
        RT_desc: "ஆதார் சேவைகள், பாஸ்போர்ட் சேவை, தபால் தலைகள் வாங்குதல்",
        "Retail & Aadhaar": "சில்லறை & ஆதார் சேவைகள்",
        "Aadhaar services, Passport Seva, stamps purchase": "ஆதார் சேவைகள், பாஸ்போர்ட் சேவை, தபால் தலைகள் வாங்குதல்",
        "Aadhaar services, Passport Seva Seva, stamps purchase": "ஆதார் சேவைகள், பாஸ்போர்ட் சேவை, தபால் தலைகள் வாங்குதல்",
        
        // Municipal Service Titles & Descriptions (Pure Tamil)
        CR: "சிவில் பதிவுகள்",
        CR_desc: "பிறப்பு சான்றிதழ், இறப்பு சான்றிதழ், திருமண பதிவு",
        "Civil Registration": "சிவில் பதிவுகள்",
        "Birth certificate, Death certificate, Marriage registration": "பிறப்பு சான்றிதழ், இறப்பு சான்றிதழ், திருமண பதிவு",
        
        TX: "வரிகள் & செலுத்துகைகள்",
        TX_desc: "சொத்து வரி, தொழில் வரி செலுத்துதல், வணிக உரிமக் கட்டணம்",
        "Taxation & Payments": "வரிகள் & செலுத்துகைகள்",
        "Property tax, professional tax payment, trade licensing dues": "சொத்து வரி, தொழில் வரி செலுத்துதல், வணிக உரிமக் கட்டணம்",
        
        PL: "அனுமதிகள் & உரிமங்கள்",
        PL_desc: "கட்டிட அனுமதி, கட்டுமான ஒப்புதல், உரிமம் புதுப்பித்தல்",
        "Permits & Licenses": "அனுமதிகள் & உரிமங்கள்",
        "Building permissions, construction approvals, license renewal": "கட்டிட அனுமதி, கட்டுமான ஒப்புதல், உரிமம் புதுப்பித்தல்",
        
        UG: "பயன்பாடுகள் & புகார்கள்",
        UG_desc: "குடிநீர் இணைப்பு, பாதாள சாக்கடை, நகராட்சி புகார்கள்",
        "Utilities & Grievances": "பயன்பாடுகள் & புகார்கள்",
        "Water connection request, drainage issues, municipal complaints": "குடிநீர் இணைப்பு, பாதாள சாக்கடை, நகராட்சி புகார்கள்",
        
        // Counter Names
        "Counter 1": "சேவை மேசை 1",
        "Counter 2": "சேவை மேசை 2",
        "Counter 3": "சேவை மேசை 3",
        "Counter 4": "சேவை மேசை 4",
        "Counter 5": "சேவை மேசை 5"
    }
};

function getLang() {
    return localStorage.getItem("userLang") || "en";
}

function getTranslation(key) {
    if (!key) return "";
    const lang = getLang();
    return (TRANSLATIONS[lang] && TRANSLATIONS[lang][key]) ? TRANSLATIONS[lang][key] : (TRANSLATIONS["en"][key] || key);
}

function applyGlobalLanguage() {
    const lang = getLang();
    document.documentElement.setAttribute("lang", lang);
    
    // Auto translate all elements with data-i18n attribute
    document.querySelectorAll("[data-i18n]").forEach(el => {
        const key = el.getAttribute("data-i18n");
        if (key) {
            const val = getTranslation(key);
            if (val) el.textContent = val;
        }
    });

    // Auto translate all input placeholders with data-i18n-placeholder
    document.querySelectorAll("[data-i18n-placeholder]").forEach(el => {
        const key = el.getAttribute("data-i18n-placeholder");
        if (key) {
            const val = getTranslation(key);
            if (val) el.placeholder = val;
        }
    });
}

function toggleLanguage() {
    const currentLang = localStorage.getItem("userLang") || "en";
    const newLang = currentLang === "en" ? "ta" : "en";
    localStorage.setItem("userLang", newLang);
    applyGlobalLanguage();
    updateLangToggleUI(newLang);
    
    // Notify page specific functions if defined
    if (typeof applyLanguage === "function") applyLanguage(newLang);
    if (typeof initKiosk === "function") initKiosk();
    if (typeof renderAdminDashboard === "function") renderAdminDashboard();
    if (typeof renderAgentWorkstation === "function") renderAgentWorkstation();
}

function updateLangToggleUI(lang) {
    const toggleBtns = document.querySelectorAll(".lang-toggle-btn");
    toggleBtns.forEach(btn => {
        if (lang === "ta") {
            btn.innerHTML = "🌐 <span class='lang-btn-text'>தமிழ் (Active)</span>";
            btn.style.borderColor = "var(--accent-primary)";
            btn.setAttribute("title", "Current Language: தமிழ். Click to switch to English.");
        } else {
            btn.innerHTML = "🌐 <span class='lang-btn-text'>English (Active)</span>";
            btn.style.borderColor = "var(--border-color)";
            btn.setAttribute("title", "Current Language: English. Click to switch to தமிழ்.");
        }
    });
}

document.addEventListener("DOMContentLoaded", () => {
    applyGlobalLanguage();
    const currentLang = localStorage.getItem("userLang") || "en";
    updateLangToggleUI(currentLang);
    
    document.querySelectorAll(".lang-toggle-btn").forEach(btn => {
        btn.addEventListener("click", toggleLanguage);
    });
});
