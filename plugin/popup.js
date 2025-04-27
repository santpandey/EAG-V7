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
            // Expecting: { weblink, text, highlight_text, highlight }
            if (!data.weblink && !data.text) {
                alert('No relevant document found.');
                return;
            }
            if (data.weblink && data.highlight) {
                // Open the link in a new tab and highlight
                chrome.tabs.create({ url: data.weblink }, function(tab) {
                    chrome.scripting.executeScript({
                        target: { tabId: tab.id },
                        func: (searchText) => {
                            // Find and highlight all occurrences of the text
                            function highlight(text) {
                                if (!text) return;
                                // Only highlight the exact query, case-insensitive
                                const regex = new RegExp(text.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'), 'gi');
                                // Walk the DOM and replace text nodes
                                function walk(node) {
                                    if (node.nodeType === 3) { // Text node
                                        const val = node.nodeValue;
                                        const span = document.createElement('span');
                                        let lastIndex = 0;
                                        let match;
                                        let replaced = false;
                                        let frag = document.createDocumentFragment();
                                        while ((match = regex.exec(val)) !== null) {
                                            if (match.index > lastIndex) {
                                                frag.appendChild(document.createTextNode(val.slice(lastIndex, match.index)));
                                            }
                                            const mark = document.createElement('span');
                                            mark.style.outline = '3px solid red';
                                            mark.style.background = 'none';
                                            mark.style.padding = '2px 4px';
                                            mark.textContent = match[0];
                                            frag.appendChild(mark);
                                            lastIndex = match.index + match[0].length;
                                            replaced = true;
                                        }
                                        if (replaced) {
                                            if (lastIndex < val.length) {
                                                frag.appendChild(document.createTextNode(val.slice(lastIndex)));
                                            }
                                            node.parentNode.replaceChild(frag, node);
                                        }
                                    } else if (node.nodeType === 1 && node.childNodes && !['SCRIPT','STYLE','NOSCRIPT','IFRAME','OBJECT'].includes(node.tagName)) {
                                        for (let i = node.childNodes.length - 1; i >= 0; i--) {
                                            walk(node.childNodes[i]);
                                        }
                                    }
                                }
                                walk(document.body);
                            }
                            highlight(searchText);
                        },
                        args: [data.highlight_text]
                    });
                });
            } else {
                // No weblink or no highlight: show text in popup
                const resultDiv = document.createElement('div');
                resultDiv.style.marginTop = '12px';
                resultDiv.style.padding = '8px';
                resultDiv.style.background = '#fffbe7';
                resultDiv.style.border = '1px solid #e2c200';
                resultDiv.style.borderRadius = '4px';
                resultDiv.textContent = data.text || data.highlight_text || 'No relevant text found.';
                document.body.appendChild(resultDiv);
            }
        } catch (err) {
            alert('Error: ' + err.message);
        }
    });
});
