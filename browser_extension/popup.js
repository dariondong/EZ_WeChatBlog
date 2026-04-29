const urlDisplay = document.getElementById("urlDisplay");
const serverUrlInput = document.getElementById("serverUrl");
const templateSelect = document.getElementById("template");
const publisherSelect = document.getElementById("publisher");
const convertBtn = document.getElementById("convertBtn");
const statusDiv = document.getElementById("status");
const statusSpinner = document.getElementById("statusSpinner");
const statusText = document.getElementById("statusText");

let currentUrl = "";
let isWeChatPage = false;

chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
  const tab = tabs[0];
  if (tab && tab.url) {
    currentUrl = tab.url;
    isWeChatPage = currentUrl.includes("mp.weixin.qq.com/s/");

    if (isWeChatPage) {
      urlDisplay.textContent = currentUrl;
      urlDisplay.classList.add("valid");
      convertBtn.disabled = false;
    } else {
      urlDisplay.textContent = "当前页面不是微信公众号文章";
      urlDisplay.classList.add("invalid");
      convertBtn.disabled = true;
    }
  }
});

chrome.storage.local.get(["serverUrl", "template", "publisher"], (data) => {
  if (data.serverUrl) serverUrlInput.value = data.serverUrl;
  if (data.template) templateSelect.value = data.template;
  if (data.publisher) publisherSelect.value = data.publisher;
});

serverUrlInput.addEventListener("change", () => {
  chrome.storage.local.set({ serverUrl: serverUrlInput.value });
});
templateSelect.addEventListener("change", () => {
  chrome.storage.local.set({ template: templateSelect.value });
});
publisherSelect.addEventListener("change", () => {
  chrome.storage.local.set({ publisher: publisherSelect.value });
});

convertBtn.addEventListener("click", async () => {
  if (!currentUrl || !isWeChatPage) return;

  const serverUrl = serverUrlInput.value.replace(/\/$/, "");
  const template = templateSelect.value;
  const publisher = publisherSelect.value;

  convertBtn.disabled = true;
  convertBtn.textContent = "转换中...";
  showStatus("loading", "正在发送请求...");

  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 60000);

    const response = await fetch(`${serverUrl}/convert`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        url: currentUrl,
        publisher: publisher,
        template: template || undefined,
        download_images: false,
      }),
      signal: controller.signal,
    });

    clearTimeout(timeoutId);
    const data = await response.json();

    if (response.ok && data.status === "ok") {
      const title = data.title || "?";
      const path = data.path || "?";
      showStatus("success", `转换成功！标题: ${title} | 路径: ${path}`);
    } else {
      showStatus("error", `转换失败: ${data.error || "未知错误"}`);
    }
  } catch (err) {
    if (err.name === "AbortError") {
      showStatus("error", "请求超时（60秒），请稍后重试");
    } else {
      showStatus("error", `连接失败: ${err.message}，请确认服务器已启动 (ez-wc serve)`);
    }
  } finally {
    convertBtn.disabled = false;
    convertBtn.textContent = "转换文章";
  }
});

function showStatus(type, message) {
  statusDiv.className = `status ${type}`;
  statusSpinner.style.display = type === "loading" ? "inline-block" : "none";
  statusText.textContent = message;
}