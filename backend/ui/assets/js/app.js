const HG_CHART_PALETTE = ["#38bdf8", "#34d399", "#fbbf24", "#f87171", "#a855f7", "#22d3ee", "#fb7185", "#f97316", "#2dd4bf", "#6366f1"];
const HG_STATE_COLORS = {
	success: "#34d399",
	warn: "#fbbf24",
	danger: "#f87171",
	info: "#38bdf8",
};

function hgParseChartDataset(raw) {
	if (!raw) return null;
	try {
		return JSON.parse(raw);
	} catch (err) {
		console.error("hg-chart parse", err);
		return null;
	}
}

function hgPickColor(entry, index) {
	const state = (entry?.State || entry?.state || "").toLowerCase();
	if (state && HG_STATE_COLORS[state]) return HG_STATE_COLORS[state];
	return HG_CHART_PALETTE[index % HG_CHART_PALETTE.length];
}

function hgSafeValue(value) {
	const num = Number(value);
	if (!Number.isFinite(num)) return 0;
	return num;
}

function hgFormatBucketLabel(bucket) {
	if (!bucket) return "";
	const date = new Date(bucket);
	if (Number.isNaN(date.getTime())) return String(bucket);
	return date.toLocaleString();
}

function hgPrepareCanvas(canvas) {
	const rect = canvas.getBoundingClientRect();
	const targetWidth = rect.width || canvas.clientWidth || 320;
	const targetHeight = rect.height || canvas.clientHeight || 240;
	const ratio = window.devicePixelRatio || 1;
	const ctx = canvas.getContext("2d");
	if (!ctx) return null;
	canvas.width = targetWidth * ratio;
	canvas.height = targetHeight * ratio;
	ctx.reset?.();
	ctx.scale(ratio, ratio);
	ctx.clearRect(0, 0, targetWidth, targetHeight);
	return {
		ctx,
		width: targetWidth,
		height: targetHeight,
		ratio,
	};
}

function hgDrawDoughnut(canvas, entries, colors) {
	const prepared = hgPrepareCanvas(canvas);
	if (!prepared) return false;
	const { ctx, width, height } = prepared;
	const total = entries.reduce((sum, entry) => sum + Math.max(0, hgSafeValue(entry)), 0);
	if (total <= 0) return false;
	const cx = width / 2;
	const cy = height / 2;
	const radius = Math.min(width, height) / 2 - 12;
	let start = -Math.PI / 2;
	entries.forEach((value, idx) => {
		const safeValue = Math.max(0, hgSafeValue(value));
		if (safeValue <= 0) return;
		const angle = (safeValue / total) * Math.PI * 2;
		ctx.beginPath();
		ctx.moveTo(cx, cy);
		ctx.fillStyle = colors[idx];
		ctx.arc(cx, cy, radius, start, start + angle, false);
		ctx.closePath();
		ctx.fill();
		start += angle;
	});
	ctx.beginPath();
	ctx.fillStyle = "rgba(15, 23, 42, 0.9)";
	ctx.arc(cx, cy, radius * 0.55, 0, Math.PI * 2, false);
	ctx.fill();
	ctx.fillStyle = "#e2e8f0";
	ctx.font = "600 16px 'Inter', 'Segoe UI', sans-serif";
	ctx.textAlign = "center";
	ctx.textBaseline = "middle";
	ctx.fillText(total.toLocaleString("es-MX"), cx, cy);
	return true;
}

function hgDrawHorizontalBar(canvas, labels, values, colors) {
	const prepared = hgPrepareCanvas(canvas);
	if (!prepared) return false;
	const { ctx, width, height } = prepared;
	const count = values.length;
	if (!count) return false;
	const maxValue = Math.max(...values, 1);
	const padding = 28;
	ctx.font = "600 13px 'Inter', 'Segoe UI', sans-serif";
	const labelWidth = Math.min(width * 0.45, Math.max(...labels.map((label) => ctx.measureText(label).width), 60) + 16);
	const barGap = 12;
	const availableHeight = height - padding * 2;
	const barHeight = Math.max(8, (availableHeight - barGap * (count - 1)) / count);
	ctx.textBaseline = "middle";
	ctx.fillStyle = "rgba(148, 163, 184, 0.25)";
	ctx.fillRect(labelWidth + padding, padding - 4, 1, height - padding * 2 + 8);
	values.forEach((value, idx) => {
		const safeValue = Math.max(0, hgSafeValue(value));
		const barLength = (safeValue / maxValue) * (width - padding * 2 - labelWidth);
		const y = padding + idx * (barHeight + barGap);
		ctx.fillStyle = "rgba(226, 232, 240, 0.82)";
		ctx.fillText(labels[idx], padding, y + barHeight / 2);
		ctx.fillStyle = colors[idx];
		const barX = labelWidth + padding + 4;
		const barY = y;
		const barW = Math.max(barLength, 4);
		const barH = barHeight;
		ctx.beginPath();
		if (typeof ctx.roundRect === "function") {
			ctx.roundRect(barX, barY, barW, barH, 6);
		} else {
			ctx.moveTo(barX, barY);
			ctx.lineTo(barX + barW, barY);
			ctx.lineTo(barX + barW, barY + barH);
			ctx.lineTo(barX, barY + barH);
			ctx.closePath();
		}
		ctx.fill();
		ctx.fillStyle = "#e2e8f0";
		ctx.font = "600 12px 'Inter', 'Segoe UI', sans-serif";
		ctx.fillText(safeValue.toLocaleString("es-MX"), labelWidth + padding + Math.max(barLength, 4) + 12, y + barHeight / 2);
	});
	return true;
}

function hgDrawLine(canvas, labels, values, color) {
	const prepared = hgPrepareCanvas(canvas);
	if (!prepared) return false;
	const { ctx, width, height } = prepared;
	const count = values.length;
	if (!count) return false;
	const padding = 36;
	const sanitized = values.map((value) => hgSafeValue(value));
	const maxValue = Math.max(...sanitized);
	const minValue = Math.min(...sanitized);
	const range = maxValue - minValue || Math.max(maxValue, 1);
	const areaWidth = width - padding * 2;
	const areaHeight = height - padding * 2;
	ctx.strokeStyle = "rgba(148, 163, 184, 0.35)";
	ctx.lineWidth = 1;
	ctx.beginPath();
	ctx.moveTo(padding, height - padding);
	ctx.lineTo(width - padding, height - padding);
	ctx.stroke();
	ctx.beginPath();
	ctx.moveTo(padding, padding);
	ctx.lineTo(padding, height - padding);
	ctx.stroke();
	const stepX = count > 1 ? areaWidth / (count - 1) : 0;
	ctx.lineWidth = 2.5;
	ctx.strokeStyle = color;
	ctx.beginPath();
	sanitized.forEach((value, idx) => {
		const normalized = (value - minValue) / range;
		const x = padding + stepX * idx;
		const y = height - padding - normalized * areaHeight;
		if (idx === 0) {
			ctx.moveTo(x, y);
		} else {
			ctx.lineTo(x, y);
		}
	});
	ctx.stroke();
	ctx.fillStyle = color;
	ctx.strokeStyle = "#0f172a";
	sanitized.forEach((value, idx) => {
		const normalized = (value - minValue) / range;
		const x = padding + stepX * idx;
		const y = height - padding - normalized * areaHeight;
		ctx.beginPath();
		ctx.arc(x, y, 4, 0, Math.PI * 2);
		ctx.fill();
		ctx.stroke();
	});
	ctx.fillStyle = "rgba(226, 232, 240, 0.72)";
	ctx.font = "600 11px 'Inter', 'Segoe UI', sans-serif";
	labels.forEach((label, idx) => {
		const x = padding + stepX * idx;
		const y = height - padding + 16;
		ctx.save();
		ctx.translate(x, y);
		ctx.rotate(-Math.PI / 6);
		ctx.textAlign = "right";
		ctx.fillText(label, 0, 0);
		ctx.restore();
	});
	return true;
}

function hgRenderDatasetChart(canvas, chartType, rawEntries, indexAxis, paletteIndex) {
	const entries = rawEntries || [];
	if (!entries.length) return false;
	if (chartType === "line") {
		const labels = entries.map((entry) => hgFormatBucketLabel(entry.Bucket || entry.bucket));
		const values = entries.map((entry) => hgSafeValue(entry.Count ?? entry.count ?? 0));
		return hgDrawLine(canvas, labels, values, HG_CHART_PALETTE[paletteIndex % HG_CHART_PALETTE.length]);
	}
	const labels = entries.map((entry, idx) => entry.Label || entry.label || entry.Code || entry.code || entry.Bucket || entry.bucket || `Item ${idx + 1}`);
	const values = entries.map((entry) => hgSafeValue(entry.Count ?? entry.count ?? 0));
	const colors = entries.map((entry, idx) => hgPickColor(entry, idx));
	if (chartType === "doughnut") {
		return hgDrawDoughnut(canvas, values, colors);
	}
	const horizontal = indexAxis === "y";
	return horizontal ? hgDrawHorizontalBar(canvas, labels, values, colors) : hgDrawHorizontalBar(canvas, labels, values, colors);
}

function hgInitDashboardCharts() {
	const canvases = document.querySelectorAll("canvas[data-hg-chart]");
	canvases.forEach((canvas, index) => {
		const entries = hgParseChartDataset(canvas.dataset.hgChart);
		if (!Array.isArray(entries) || !entries.length) {
			return;
		}
		const chartType = canvas.dataset.hgType || "bar";
		const indexAxis = canvas.dataset.hgIndexAxis || "x";
		const rendered = hgRenderDatasetChart(canvas, chartType, entries, indexAxis, index);
		if (rendered) {
			const card = canvas.closest(".hg-chart-card");
			if (card) {
				card.classList.add("has-chart");
			}
		}
	});
}

document.addEventListener("DOMContentLoaded", () => {
	const currentPath = window.location.pathname.replace(/\/$/, "");
	document.querySelectorAll(".hg-sidebar a").forEach((link) => {
		const href = link.getAttribute("href") || "";
		if (!href) return;
		const normalized = href.replace(/\/$/, "");
		if (normalized === "") return;
		if (normalized === currentPath || currentPath.startsWith(normalized + "/")) {
			link.classList.add("is-active");
		}
	});

	document.querySelectorAll(".hg-flash").forEach((flash, index) => {
		const timeout = 4800 + index * 600;
		setTimeout(() => {
			flash.classList.add("is-dismissed");
			flash.addEventListener(
				"transitionend",
				() => {
					flash.remove();
				},
				{ once: true }
			);
		}, timeout);
		flash.addEventListener("click", () => {
			flash.classList.add("is-dismissed");
		});
	});

	document.querySelectorAll("form[data-hg-confirm]").forEach((form) => {
		form.addEventListener("submit", (event) => {
			const message = form.getAttribute("data-hg-confirm") || "¿Confirmar acción?";
			if (!window.confirm(message)) {
				event.preventDefault();
			}
		});
	});

	document.querySelectorAll("form.hg-autoform select").forEach((select) => {
		select.addEventListener("change", () => {
			const form = select.closest("form.hg-autoform");
			if (!form) {
				return;
			}
			form.submit();
		});
	});

	hgInitDashboardCharts();
});
