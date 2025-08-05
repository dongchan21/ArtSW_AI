async function loadProblem() {
  const mode = document.getElementById("mode").value;
  const resultArea = document.getElementById("result");

  try {
    const res = await fetch(`http://localhost:8000/api/problems/story_001?mode=${mode}`);
    const data = await res.json();

    resultArea.textContent = JSON.stringify(data, null, 2);
  } catch (err) {
    resultArea.textContent = "❌ 에러 발생: " + err.message;
  }
}
