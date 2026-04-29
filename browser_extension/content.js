if (window.__ez_wc_injected) {
  // already injected
} else {
  window.__ez_wc_injected = true;

  const DEFAULT_API_URL = "http://localhost:5000";

  function getApiUrl() {
    return new Promise((resolve) => {
      chrome.storage.local.get(["serverUrl"], (data) => {
        resolve((data.serverUrl || DEFAULT_API_URL).replace(/\/$/, ""));
      });
    });
  }

  function createButton(apiUrl) {
    const btn = document.createElement("button");
    btn.id = "ez-wc-convert-btn";
    btn.textContent = "\u{1F4DD} 转为 Markdown";
    btn.title = "EZ WeChatBlog: 一键转换";
    btn.addEventListener("click", async (e) => {
      e.preventDefault();
      e.stopPropagation();
      btn.disabled = true;
      btn.textContent = "转换中...";

      try {
        const resp = await fetch(`${apiUrl}/convert`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            url: window.location.href,
            download_images: false,
          }),
        });
        const data = await resp.json();
        if (resp.ok && data.status === "ok") {
          btn.textContent = "\u2705 转换成功";
          btn.style.background = "#28a745";
        } else {
          btn.textContent = "\u274C 失败";
          btn.style.background = "#dc3545";
          console.error("EZ WeChatBlog error:", data.error);
        }
      } catch (err) {
        btn.textContent = "\u274C 连接失败";
        btn.style.background = "#dc3545";
        console.error("EZ WeChatBlog connection error:", err);
      }

      setTimeout(() => {
        btn.disabled = false;
        btn.textContent = "\u{1F4DD} 转为 Markdown";
        btn.style.background = "";
      }, 3000);
    });

    return btn;
  }

  async function inject() {
    const apiUrl = await getApiUrl();
    const profile = document.querySelector("#profileBt") ||
                    document.querySelector(".profile_inner_wrp") ||
                    document.querySelector("#js_name");
    if (profile && !document.getElementById("ez-wc-convert-btn")) {
      const btn = createButton(apiUrl);
      profile.parentElement.insertBefore(btn, profile.nextSibling);
    }
  }

  if (document.readyState === "complete") {
    inject();
  } else {
    window.addEventListener("load", inject);
  }
  setTimeout(inject, 2000);
}