const beforeInput = document.getElementById("beforeImage");
const afterInput = document.getElementById("afterImage");
const analyzeBtn = document.getElementById("analyzeBtn");

const beforePreview = document.getElementById("beforePreview");
const afterPreview = document.getElementById("afterPreview");

const beforeLabel = document.getElementById("beforeLabel");
const afterLabel = document.getElementById("afterLabel");

const terminal = document.getElementById("terminal");

let eventSource = null;

/* Terminal logging */
function addLog(message) {
    let status = "info"; // default = white

    const lower = message.toLowerCase();

    if (
        lower.includes("complete") ||
        lower.includes("completed") ||
        lower.includes("pixels")
    ) {
        status = "success"; // green
    }
    else if (
        lower.includes("error") ||
        lower.includes("failed") ||
        lower.includes("exception")
    ) {
        status = "error"; // red
    }

    const line = document.createElement("div");
    line.className = `terminal-line ${status}`;
    line.innerText = message;
    terminal.appendChild(line);
    terminal.scrollTop = terminal.scrollHeight;
}

let dotInterval = null;
function startDots() {
    stopDots();
    let dots = "";
    dotInterval = setInterval(() => {
        dots = dots.length < 3 ? dots + "." : "";
        const last = terminal.lastElementChild;
        if (last) last.innerText = last.innerText.split(".")[0] + dots;
    }, 500);
}

function stopDots() {
    if (dotInterval) {
        clearInterval(dotInterval);
        dotInterval = null;
    }
}

function handleFileSelect(input, preview, label) {
    const file = input.files[0];
    if (!file) return;

    label.innerText = file.name;

    if (file.type.startsWith("image/") && !file.name.endsWith(".tif")) {
        preview.src = URL.createObjectURL(file);
        preview.style.display = "block";
    }
}

beforeInput.addEventListener("change", () =>
    handleFileSelect(beforeInput, beforePreview, beforeLabel)
);

afterInput.addEventListener("change", () =>
    handleFileSelect(afterInput, afterPreview, afterLabel)
);

/* GeoJSON viewer */
function createGeoJSONContainer(geojson) {
    const existing = document.getElementById("geojsonContainer");
    if (existing) existing.remove();

    const container = document.createElement("div");
    container.id = "geojsonContainer";
    container.className = "geojson-container";

    const header = document.createElement("div");
    header.className = "geojson-header";

    const title = document.createElement("h3");
    title.innerText = "GeoJSON Output";

    const btn = document.createElement("button");
    btn.className = "geojson-download";
    btn.innerText = "Download";

    btn.onclick = () => {
        const blob = new Blob(
            [JSON.stringify(geojson, null, 2)],
            { type: "application/json" }
        );
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = "change_output.geojson";
        a.click();
        URL.revokeObjectURL(url);
    };

    header.appendChild(title);
    header.appendChild(btn);

    const pre = document.createElement("pre");
    pre.innerText = JSON.stringify(geojson, null, 2);

    container.appendChild(header);
    container.appendChild(pre);

    analyzeBtn.parentNode.insertBefore(container, analyzeBtn);
}

/* SSE Log Stream */
function startLogStream() {
    if (eventSource) eventSource.close();

    eventSource = new EventSource("/logs");

    eventSource.onmessage = (event) => {
        const msg = event.data;

        if (msg === ".") return;

        if (msg === "__ANALYSIS_DONE__") {
            stopDots();
            eventSource.close();
            return;
        }

        addLog(msg, "info");
        startDots();
    };

    eventSource.onerror = () => {
        stopDots();
        eventSource.close();
    };
}

analyzeBtn.addEventListener("click", () => {
    if (!beforeInput.files[0] || !afterInput.files[0]) {
        addLog("Upload both images", "error");
        return;
    }

    terminal.innerHTML = "";
    addLog("Analysis started", "info");

    startLogStream();

    const formData = new FormData();
    formData.append("before", beforeInput.files[0]);
    formData.append("after", afterInput.files[0]);

    fetch("/detect-change", {
        method: "POST",
        body: formData
    })
    .then(res => res.json())
    .then(data => {
        stopDots();

        if (data.error) {
            addLog(data.error, "error");
            return;
        }

        /* Backend previews */
        if (data.before_preview) {
            beforePreview.src =
                "data:image/png;base64," + data.before_preview;
            beforePreview.style.display = "block";
        }

        if (data.after_preview) {
            afterPreview.src =
                "data:image/png;base64," + data.after_preview;
            afterPreview.style.display = "block";
        }

        if (data.geojson) {
            createGeoJSONContainer(data.geojson);
        }
    })
    .catch(err => {
        stopDots();
        console.error(err);
        addLog("Processing failed", "error");
    });
});
