// Extract content and URL, ignoring WhatsApp and Gmail
(function() {
    const url = window.location.href;
    const lowerUrl = url.toLowerCase();
    if (
        lowerUrl.includes('web.whatsapp.com') ||
        lowerUrl.includes('mail.google.com') ||
        lowerUrl.includes('accounts.google.com')
    ) {
        return; // Ignore WhatsApp and Gmail
    }

    // Extract visible text content
    const content = document.body ? document.body.innerText : '';
    if (!content || content.trim().length < 20) return; // Ignore empty/very short pages

    // Send to background script
    chrome.runtime.sendMessage({
        type: 'EAG_CAPTURE',
        data: {
            url: url,
            content: content
        }
    });
})();
