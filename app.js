document.getElementById("uploadBtn").onclick = () => {
  document.getElementById("audioInput").click();
};

document.getElementById("audioInput").onchange = async (event) => {
  const file = event.target.files[0];
  if (!file) return;

  const formData = new FormData();
  formData.append("file", file);

  // IMPORTANT: replace with your computer's local IP
  const backendUrl = "http://192.168.4.21/mobile/analyze";

  const response = await fetch(backendUrl, {
    method: "POST",
    body: formData
  });

  const json = await response.json();
  document.getElementById("results").textContent =
    JSON.stringify(json, null, 2);
};