/**
 * Centralized Kiosk Operating Configuration System
 * Calculates dynamic daily token caps based on center operating hours,
 * break durations, active counters, and average service completion times.
 *
 * Formula: Total Daily Tokens = ((Operating Mins - Break Mins) / Avg Service Mins) * Active Counters
 */

const KIOSK_CONFIG = {
  BANK: {
    name: "Bank Branch",
    openTime: "09:30",
    closeTime: "16:00", // 4:00 PM (390 total mins)
    breakDurationMinutes: 30, // 360 effective working mins
    services: {
      AC: {
        code: "AC",
        name: "Account Opening & KYC",
        desc: "Open new account, submit documentations, update address",
        icon: "👤",
        avgServiceTimeMins: 10,
        activeCounters: 2
      },
      CS: {
        code: "CS",
        name: "Cash Transactions",
        desc: "Deposit cash, withdraw money, process cheques",
        icon: "💵",
        avgServiceTimeMins: 5,
        activeCounters: 3
      },
      AD: {
        code: "AD",
        name: "Aadhaar & Loans",
        desc: "Aadhaar update, loan applications, FD/RD setups",
        icon: "💼",
        avgServiceTimeMins: 12,
        activeCounters: 2
      }
    }
  },
  MUNICIPAL: {
    name: "Municipal Corporation",
    openTime: "10:00",
    closeTime: "17:00", // 5:00 PM (420 total mins)
    breakDurationMinutes: 45, // 375 effective working mins
    services: {
      CR: {
        code: "CR",
        name: "Civil Registration",
        desc: "Birth certificate, Death certificate, Marriage registration",
        icon: "👶",
        avgServiceTimeMins: 12,
        activeCounters: 2
      },
      PL: {
        code: "PL",
        name: "Permits & Licenses",
        desc: "Building permissions, construction approvals, license renewal",
        icon: "🏗️",
        avgServiceTimeMins: 15,
        activeCounters: 2
      },
      TX: {
        code: "TX",
        name: "Taxation & Payments",
        desc: "Property tax, professional tax payment, trade licensing dues",
        icon: "🪙",
        avgServiceTimeMins: 10,
        activeCounters: 2
      },
      UG: {
        code: "UG",
        name: "Utilities & Grievances",
        desc: "Water connection request, drainage issues, municipal complaints",
        icon: "🛠️",
        avgServiceTimeMins: 10,
        activeCounters: 2
      }
    }
  },
  ESEVAI: {
    name: "E-Sevai Maiyam",
    openTime: "09:00",
    closeTime: "17:00", // 8:00 PM (480 total mins)
    breakDurationMinutes: 30, // 450 effective working mins
    services: {
      RV: {
        code: "RV",
        name: "Revenue Certificates",
        desc: "Community, Income, Nativity, First Graduate certificates",
        icon: "📝",
        avgServiceTimeMins: 8,
        activeCounters: 3
      },
      SS: {
        code: "SS",
        name: "Pension Schemes",
        desc: "Old Age Pension, Destitute Widow, Disability pension",
        icon: "👵",
        avgServiceTimeMins: 10,
        activeCounters: 2
      },
      LD: {
        code: "LD",
        name: "Land & Utilities",
        desc: "Patta transfer, Chitta, A-Register, Electricity bills",
        icon: "🏠",
        avgServiceTimeMins: 12,
        activeCounters: 2
      }
    }
  },
  POST_OFFICE: {
    name: "Post Office",
    openTime: "09:00",
    closeTime: "16:00", // 4:00 PM (420 total mins)
    breakDurationMinutes: 30, // 390 effective working mins
    services: {
      RT: {
        code: "RT",
        name: "Retail & Aadhaar",
        desc: "Aadhaar services, Passport Seva, stamps purchase",
        icon: "🛍️",
        avgServiceTimeMins: 15,
        activeCounters: 2
      },
      MP: {
        code: "MP",
        name: "Mails & Parcels",
        desc: "Speed Post, Registered Post, domestic/international mail",
        icon: "📦",
        avgServiceTimeMins: 6,
        activeCounters: 2
      },
      SB: {
        code: "SB",
        name: "Savings Bank & Money transfer",
        desc: "Post office savings account, IPPB, Money orders",
        icon: "🏦",
        avgServiceTimeMins: 8,
        activeCounters: 2
      },
      INS: {
        code: "INS",
        name: "Postal Life Insurance",
        desc: "PLI, RPLI, Pradhan Mantri Bima Yojana applications",
        icon: "🛡️",
        avgServiceTimeMins: 12,
        activeCounters: 1
      }
    }
  }
};

/**
 * Calculates dynamic token limit based on formula:
 * Total Daily Tokens = ((Operating Mins - Break Mins) / Avg Service Mins) * Active Counters
 */
function calculateTokenLimit(openTime, closeTime, breakMins, avgServiceMins, activeCounters) {
    if (!openTime || !closeTime || avgServiceMins <= 0 || activeCounters <= 0) return 100;
    
    const [openH, openM] = openTime.split(':').map(Number);
    const [closeH, closeM] = closeTime.split(':').map(Number);
    
    const totalOperatingMins = (closeH * 60 + closeM) - (openH * 60 + openM);
    const effectiveWorkingMins = Math.max(0, totalOperatingMins - breakMins);
    
    return Math.floor((effectiveWorkingMins / avgServiceMins) * activeCounters);
}

/**
 * Returns complete service details including computed daily token limit
 */
function getServiceConfig(officeType, serviceCode) {
    const office = KIOSK_CONFIG[officeType] || KIOSK_CONFIG.BANK;
    const service = office.services[serviceCode];
    if (!service) return null;
    
    const dailyLimit = calculateTokenLimit(
        office.openTime,
        office.closeTime,
        office.breakDurationMinutes,
        service.avgServiceTimeMins,
        service.activeCounters
    );
    
    return {
        ...service,
        openTime: office.openTime,
        closeTime: office.closeTime,
        breakDurationMinutes: office.breakDurationMinutes,
        dailyLimit: dailyLimit
    };
}

// Export for module or browser window global
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { KIOSK_CONFIG, calculateTokenLimit, getServiceConfig };
}
