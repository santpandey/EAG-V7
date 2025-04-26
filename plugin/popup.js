document.addEventListener('DOMContentLoaded', function() {
    // Clear previous state
    document.getElementById('queryBox').value = '';
    // Add close button logic
    document.getElementById('closeBtn').addEventListener('click', function() {
        window.close();
    });
    document.getElementById('submitBtn').addEventListener('click', async function() {
        const query = document.getElementById('queryBox').value.trim();
        if (!query) {
            alert('Please enter a query.');
            return;
        }
        // Call backend GET endpoint (assuming /search_documents?query=...)
        try {
            const resp = await fetch(`http://localhost:8000/search_documents?query=${encodeURIComponent(query)}`);
            if (!resp.ok) throw new Error('No response from backend');
            const data = await resp.json();
            // Expecting: { weblink: ..., text: ... }
            if (!data.weblink || !data.text) {
                alert('No relevant document found.');
                return;
            }
            // Open the link in a new tab and highlight
            chrome.tabs.create({ url: data.weblink }, function(tab) {
                // Wait for tab to load, then inject script to highlight text
                chrome.scripting.executeScript({
                    target: { tabId: tab.id },
                    func: (searchText) => {
                        // Find and highlight all occurrences of the text
                        function highlight(text) {
                            const innerHTML = document.body.innerHTML;
                            const regex = new RegExp(text.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'gi');
                            document.body.innerHTML = innerHTML.replace(regex, match => `<span style="outline: 2px solid red; background: yellow;">${match}</span>`);
                        }
                        highlight(searchText);
                    },
                    args: [data.text]
                });
            });
        } catch (err) {
            alert('Error: ' + err.message);
        }
    });
});
