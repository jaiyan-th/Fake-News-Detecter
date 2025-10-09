async function checkNews() {
  const text = document.getElementById("newsInput").value;
  const resultDiv = document.getElementById("result");

  if (!text.trim()) {
    resultDiv.innerHTML = "❌ Please enter some news text.";
    return;
  }

  const response = await fetch("http://127.0.0.1:5000/predict", {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify({ text: text })
  });

  const data = await response.json();
  const label = data.prediction.toUpperCase();
  const confidence = (data.confidence * 100).toFixed(2);

  resultDiv.innerHTML = `🧠 Prediction: <b>${label}</b> <br>🔍 Confidence: ${confidence}%`;
}
