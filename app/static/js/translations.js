
const translations = {
    en: {
        workspace: "WORKSPACE",
        dashboard: "Dashboard",
        heatmap: "Heat Map",
        analysis: "Area Analysis",
        predictions: "AI Predictions",
        recommendations: "Recommendations",
        reports: "Reports",
        system: "SYSTEM",
        settings: "Settings",
        welcome: "Welcome to your climate intelligence platform.",
        location: "SELECTED LOCATION",
        sampleNotice: "Demonstration dashboard · Sample data",
        temperature: "Temperature",
        temperatureNote: "Average sample temperature",
        riskLevel: "Heat Risk Level",
        riskNote: "Demonstration risk classification",
        vegetation: "Vegetation Coverage",
        vegetationNote: "Sample green coverage",
        hotspots: "High Risk Areas",
        hotspotNote: "Sample identified locations",
        mapDescription: "Urban heat-risk visualization",
        riskDistribution: "Risk Distribution",
        riskDescription: "Sample area classification",
        low: "Low Risk",
        medium: "Medium Risk",
        high: "High Risk",
        recommendationDescription: "Suggested actions for urban cooling",
        recommendationOne: "Increase tree plantation in high-risk areas.",
        recommendationTwo: "Promote cool roofs on buildings.",
        recommendationThree: "Develop green spaces and urban gardens.",
        footer: "Climate Intelligence Platform",
        sampleData: "SAMPLE DATA"
    },

    mr: {
        workspace: "कार्यस्थळ",
        dashboard: "डॅशबोर्ड",
        heatmap: "उष्णता नकाशा",
        analysis: "क्षेत्र विश्लेषण",
        predictions: "AI अंदाज",
        recommendations: "शिफारसी",
        reports: "अहवाल",
        system: "प्रणाली",
        settings: "सेटिंग्ज",
        welcome: "तुमच्या हवामान माहिती प्लॅटफॉर्ममध्ये स्वागत आहे.",
        location: "निवडलेले ठिकाण",
        sampleNotice: "प्रात्यक्षिक डॅशबोर्ड · नमुना डेटा",
        temperature: "तापमान",
        temperatureNote: "सरासरी नमुना तापमान",
        riskLevel: "उष्णतेचा धोका स्तर",
        riskNote: "प्रात्यक्षिक धोका वर्गीकरण",
        vegetation: "वनस्पती आच्छादन",
        vegetationNote: "नमुना हरित क्षेत्र",
        hotspots: "उच्च धोका क्षेत्रे",
        hotspotNote: "ओळखलेली नमुना ठिकाणे",
        mapDescription: "शहरी उष्णता धोक्याचे दृश्य",
        riskDistribution: "धोका वितरण",
        riskDescription: "नमुना क्षेत्र वर्गीकरण",
        low: "कमी धोका",
        medium: "मध्यम धोका",
        high: "जास्त धोका",
        recommendationDescription: "शहर थंड ठेवण्यासाठी सुचवलेल्या उपाययोजना",
        recommendationOne: "जास्त धोका असलेल्या भागात वृक्षारोपण वाढवा.",
        recommendationTwo: "इमारतींवर थंड छतांचा वापर प्रोत्साहित करा.",
        recommendationThree: "हिरवीगार जागा आणि शहरी उद्याने विकसित करा.",
        footer: "हवामान माहिती प्लॅटफॉर्म",
        sampleData: "नमुना डेटा"
    },

    hi: {
        workspace: "कार्यस्थल",
        dashboard: "डैशबोर्ड",
        heatmap: "हीट मैप",
        analysis: "क्षेत्र विश्लेषण",
        predictions: "AI अनुमान",
        recommendations: "सुझाव",
        reports: "रिपोर्ट",
        system: "सिस्टम",
        settings: "सेटिंग्स",
        welcome: "आपके जलवायु सूचना प्लेटफॉर्म में स्वागत है।",
        location: "चयनित स्थान",
        sampleNotice: "डेमो डैशबोर्ड · नमूना डेटा",
        temperature: "तापमान",
        temperatureNote: "औसत नमूना तापमान",
        riskLevel: "गर्मी का जोखिम स्तर",
        riskNote: "डेमो जोखिम वर्गीकरण",
        vegetation: "वनस्पति क्षेत्र",
        vegetationNote: "नमूना हरित क्षेत्र",
        hotspots: "उच्च जोखिम वाले क्षेत्र",
        hotspotNote: "पहचाने गए नमूना स्थान",
        mapDescription: "शहरी गर्मी जोखिम का दृश्य",
        riskDistribution: "जोखिम वितरण",
        riskDescription: "नमूना क्षेत्र वर्गीकरण",
        low: "कम जोखिम",
        medium: "मध्यम जोखिम",
        high: "उच्च जोखिम",
        recommendationDescription: "शहर को ठंडा रखने के लिए सुझाए गए उपाय",
        recommendationOne: "उच्च जोखिम वाले क्षेत्रों में अधिक पेड़ लगाएँ।",
        recommendationTwo: "इमारतों पर ठंडी छतों को बढ़ावा दें।",
        recommendationThree: "हरित क्षेत्र और शहरी उद्यान विकसित करें।",
        footer: "जलवायु सूचना प्लेटफॉर्म",
        sampleData: "नमूना डेटा"
    }
};

function applyLanguage(language) {
    const selectedLanguage = translations[language] ? language : "en";

    document.documentElement.lang = selectedLanguage;

    document.querySelectorAll("[data-i18n]").forEach(element => {
        const key = element.getAttribute("data-i18n");

        if (translations[selectedLanguage][key]) {
            element.textContent = translations[selectedLanguage][key];
        }
    });

    const sampleTag = document.querySelector(".map-card .status-tag");

    if (sampleTag) {
        sampleTag.textContent = translations[selectedLanguage].sampleData;
    }

    localStorage.setItem("urbanHeatLanguage", selectedLanguage);
}

document.addEventListener("DOMContentLoaded", function () {
    const languageSelect = document.getElementById("languageSelect");

    if (!languageSelect) return;

    const savedLanguage = localStorage.getItem("urbanHeatLanguage") || "en";

    languageSelect.value = savedLanguage;
    applyLanguage(savedLanguage);

    languageSelect.addEventListener("change", function () {
        applyLanguage(this.value);
    });
});
