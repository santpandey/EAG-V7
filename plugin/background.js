// Listen for messages from content script and forward to backend
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.type === "EAG_CAPTURE" && message.data) {
    // Send to backend endpoint
    fetch("http://127.0.0.1:8000/save_web_content", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        url: message.data.url,
        content: message.data.content,
      }),
    })
      .then((response) => {
        // Optionally handle response
      })
      .catch((err) => {
        // Optionally handle error
        console.error("Failed to save web content:", err);
      });
  }
});
