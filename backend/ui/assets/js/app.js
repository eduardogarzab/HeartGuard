const HG_COLOR_BASE = "#38bdf8";
const HG_COLOR_PALETTE = ["#38bdf8", "#0ea5e9", "#0284c7", "#0369a1", "#075985", "#0c4a6e", "#1d7ed6", "#60a5fa", "#1dc7ff", "#4db5ff"];
const HG_STATE_COLORS = {
    success: "#22c55e",
    warn: "#eab308",
    danger: "#f87171",
    info: HG_COLOR_BASE,
};

function hgGetPaletteColor(index, offset = 0) {
    const paletteLength = HG_COLOR_PALETTE.length || 1;
    const normalizedIndex = (((offset + index) % paletteLength) + paletteLength) % paletteLength;
    return HG_COLOR_PALETTE[normalizedIndex];
}

function hgHexToRgb(hex) {
    const normalized = hex.replace(/[^0-9a-f]/gi, "");
    if (normalized.length === 3) {
        const r = normalized[0];
        const g = normalized[1];
        const b = normalized[2];
        return {
            r: parseInt(`${r}${r}`, 16),
            g: parseInt(`${g}${g}`, 16),
            b: parseInt(`${b}${b}`, 16),
        };
    }
    if (normalized.length >= 6) {
        return {
            r: parseInt(normalized.slice(0, 2), 16),
            g: parseInt(normalized.slice(2, 4), 16),
            b: parseInt(normalized.slice(4, 6), 16),
        };
    }
    return { r: 56, g: 189, b: 248 };
}

function hgColorWithAlpha(hex, alpha) {
    const { r, g, b } = hgHexToRgb(hex);
    return `rgba(${r}, ${g}, ${b}, ${alpha})`;
}

let hgTooltipEl = null;

function hgParseChartDataset(raw) {
    if (!raw) return null;
    try {
        return JSON.parse(raw);
    } catch (err) {
        console.error("hg-chart parse", err);
        return null;
    }
}

function hgPickColor(entry, index, offset) {
    const state = (entry?.State || entry?.state || "").toLowerCase();
    if (state && state !== "info" && HG_STATE_COLORS[state]) {
        return HG_STATE_COLORS[state];
    }
    return hgGetPaletteColor(index, offset);
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

function hgFormatBucketLabelParts(bucket) {
    const fallback = { primary: bucket ? String(bucket) : "", secondary: "", raw: bucket };
    if (!bucket) return fallback;
    const date = new Date(bucket);
    if (Number.isNaN(date.getTime())) {
        return fallback;
    }
    return {
        primary: date.toLocaleDateString("es-MX"),
        secondary: date.toLocaleTimeString("es-MX"),
        raw: date,
    };
}

function hgEnsureTooltip() {
    if (!hgTooltipEl) {
        hgTooltipEl = document.createElement("div");
        hgTooltipEl.className = "hg-chart-tooltip";
        document.body.appendChild(hgTooltipEl);
    }
    return hgTooltipEl;
}

function hgShowTooltip(x, y, html) {
    const tooltip = hgEnsureTooltip();
    tooltip.innerHTML = html;
    tooltip.style.transform = `translate3d(${x + 14}px, ${y + 18}px, 0)`;
    tooltip.classList.add("is-visible");
}

function hgHideTooltip() {
    if (!hgTooltipEl) return;
    hgTooltipEl.classList.remove("is-visible");
    hgTooltipEl.style.transform = "translate3d(-9999px, -9999px, 0)";
}

function hgNormalizeAngle(angle) {
    const tau = Math.PI * 2;
    return ((angle % tau) + tau) % tau;
}

function hgEllipsize(ctx, text, maxWidth) {
    if (!text) return "";
    if (ctx.measureText(text).width <= maxWidth) return text;
    let truncated = text;
    while (truncated.length > 1 && ctx.measureText(`${truncated}…`).width > maxWidth) {
        truncated = truncated.slice(0, -1);
    }
    return `${truncated}…`;
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

function hgDrawDoughnut(canvas, dataset, activeIndex) {
    const prepared = hgPrepareCanvas(canvas);
    if (!prepared) return null;
    const { ctx, width, height } = prepared;
    const { values, colors, labels } = dataset;
    const total = values.reduce((sum, entry) => sum + Math.max(0, hgSafeValue(entry)), 0);
    if (total <= 0) return null;
    const cx = width / 2;
    const cy = height / 2;
    const baseOuter = Math.max(Math.min(width, height) / 2 - 18, 48);
    const baseInner = Math.max(baseOuter * 0.6, baseOuter - 46);
    const activeIdx = Number.isFinite(activeIndex) ? activeIndex : null;
    let start = -Math.PI / 2;
    const segments = [];
    values.forEach((value, idx) => {
        const safeValue = Math.max(0, hgSafeValue(value));
        if (safeValue <= 0) {
            return;
        }
        const angle = (safeValue / total) * Math.PI * 2;
        const end = start + angle;
        const startNorm = hgNormalizeAngle(start);
        const endNorm = hgNormalizeAngle(end);
        const isActive = activeIdx === idx;
        const outer = baseOuter + (isActive ? 10 : 0);
        const inner = Math.max(baseInner - (isActive ? 8 : 0), baseInner * 0.75);
        ctx.save();
        ctx.beginPath();
        if (isActive) {
            ctx.shadowColor = "rgba(56, 189, 248, 0.45)";
            ctx.shadowBlur = 28;
        } else {
            ctx.shadowColor = "transparent";
            ctx.shadowBlur = 0;
        }
        ctx.fillStyle = colors[idx];
        ctx.arc(cx, cy, outer, start, end, false);
        ctx.arc(cx, cy, inner, end, start, true);
        ctx.closePath();
        ctx.fill();
        ctx.restore();
        if (isActive) {
            ctx.save();
            ctx.lineWidth = 2;
            ctx.strokeStyle = "rgba(255, 255, 255, 0.85)";
            ctx.beginPath();
            ctx.arc(cx, cy, outer, start, end, false);
            ctx.stroke();
            ctx.restore();
        }
        segments.push({
            index: idx,
            start: startNorm,
            end: endNorm,
            wrap: endNorm < startNorm,
            value: safeValue,
            percent: safeValue / total,
            label: labels[idx],
            color: colors[idx],
        });
        start = end;
    });
    const innerCircle = baseInner * 0.82;
    ctx.beginPath();
    ctx.fillStyle = "rgba(15, 23, 42, 0.92)";
    ctx.arc(cx, cy, innerCircle, 0, Math.PI * 2, false);
    ctx.fill();
    const activeSegment = Number.isFinite(activeIdx) ? segments.find((segment) => segment.index === activeIdx) : null;
    const primaryValue = (activeSegment ? activeSegment.value : total).toLocaleString("es-MX");
    ctx.textAlign = "center";
    ctx.textBaseline = "middle";
    ctx.fillStyle = "#f8fafc";
    ctx.font = "600 17px 'Inter', 'Segoe UI', sans-serif";
    ctx.fillText(primaryValue, cx, cy - (activeSegment ? 8 : 4));
    ctx.textBaseline = "top";
    ctx.font = "500 11px 'Inter', 'Segoe UI', sans-serif";
    ctx.fillStyle = "rgba(148, 163, 184, 0.84)";
    const labelText = activeSegment ? hgEllipsize(ctx, activeSegment.label || "", innerCircle * 1.6) : "Total";
    ctx.fillText(labelText || "Total", cx, cy + 2);
    if (activeSegment) {
        ctx.font = "500 10px 'Inter', 'Segoe UI', sans-serif";
        ctx.fillStyle = "rgba(148, 163, 184, 0.7)";
        const percentText = `${Math.round(activeSegment.percent * 1000) / 10}%`;
        ctx.fillText(percentText, cx, cy + 16);
    }
    return {
        cx,
        cy,
        innerRadius: baseInner,
        outerRadius: baseOuter,
        segments,
        total,
    };
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
    const measured = labels.map((label) => ctx.measureText(label).width);
    const labelWidth = Math.min(width * 0.45, Math.max(...measured, 60) + 24);
    const barGap = 12;
    const availableHeight = height - padding * 2;
    const barHeight = Math.max(12, (availableHeight - barGap * (count - 1)) / count);
    ctx.textBaseline = "middle";
    ctx.fillStyle = "rgba(148, 163, 184, 0.18)";
    ctx.fillRect(labelWidth + padding, padding - 6, 1, height - padding * 2 + 12);
    values.forEach((value, idx) => {
        const safeValue = Math.max(0, hgSafeValue(value));
        const barLength = (safeValue / maxValue) * (width - padding * 2 - labelWidth);
        const y = padding + idx * (barHeight + barGap);
        ctx.fillStyle = "rgba(226, 232, 240, 0.82)";
        const text = hgEllipsize(ctx, labels[idx], labelWidth - 16);
        ctx.fillText(text, padding, y + barHeight / 2);
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
    const paddingX = 56;
    const paddingY = 48;
    const sanitized = values.map((value) => hgSafeValue(value));
    const maxValue = Math.max(...sanitized);
    const minValue = Math.min(...sanitized);
    const range = maxValue - minValue || Math.max(maxValue, 1);
    const chartLeft = paddingX;
    const chartRight = width - paddingX;
    const chartTop = paddingY;
    const chartBottom = height - paddingY;
    const areaWidth = chartRight - chartLeft;
    const areaHeight = chartBottom - chartTop;
    ctx.lineWidth = 1;
    ctx.strokeStyle = "rgba(148, 163, 184, 0.28)";
    const gridLines = 4;
    for (let i = 0; i <= gridLines; i += 1) {
        const ratio = i / gridLines;
        const y = chartBottom - areaHeight * ratio;
        ctx.beginPath();
        ctx.moveTo(chartLeft, y);
        ctx.lineTo(chartRight, y);
        ctx.stroke();
    }
    ctx.beginPath();
    ctx.moveTo(chartLeft, chartBottom);
    ctx.lineTo(chartRight, chartBottom);
    ctx.strokeStyle = "rgba(148, 163, 184, 0.45)";
    ctx.stroke();
    ctx.beginPath();
    ctx.moveTo(chartLeft, chartTop);
    ctx.lineTo(chartLeft, chartBottom);
    ctx.stroke();
    const stepX = count > 1 ? areaWidth / (count - 1) : 0;
    ctx.lineWidth = 2.5;
    ctx.strokeStyle = color;
    ctx.beginPath();
    sanitized.forEach((value, idx) => {
        const normalized = (value - minValue) / range;
        const x = chartLeft + stepX * idx;
        const y = chartBottom - normalized * areaHeight;
        if (idx === 0) {
            ctx.moveTo(x, y);
        } else {
            ctx.lineTo(x, y);
        }
    });
    ctx.stroke();
    ctx.lineTo(chartRight, chartBottom);
    ctx.lineTo(chartLeft, chartBottom);
    ctx.closePath();
    const gradient = ctx.createLinearGradient(0, chartTop, 0, chartBottom);
    gradient.addColorStop(0, hgColorWithAlpha(color, 0.28));
    gradient.addColorStop(1, hgColorWithAlpha(color, 0));
    ctx.fillStyle = gradient;
    ctx.fill();
    ctx.fillStyle = color;
    ctx.strokeStyle = "#0f172a";
    sanitized.forEach((value, idx) => {
        const normalized = (value - minValue) / range;
        const x = chartLeft + stepX * idx;
        const y = chartBottom - normalized * areaHeight;
        ctx.beginPath();
        ctx.arc(x, y, 4, 0, Math.PI * 2);
        ctx.fill();
        ctx.stroke();
    });
    ctx.fillStyle = "rgba(148, 163, 184, 0.75)";
    ctx.font = "600 11px 'Inter', 'Segoe UI', sans-serif";
    ctx.textAlign = "right";
    ctx.textBaseline = "middle";
    const tickCount = Math.min(5, Math.max(2, sanitized.length));
    for (let i = 0; i <= tickCount; i += 1) {
        const ratio = i / tickCount;
        const value = minValue + range * ratio;
        const y = chartBottom - areaHeight * ratio;
        ctx.fillText(Math.round(value).toLocaleString("es-MX"), chartLeft - 8, y);
    }
    ctx.fillStyle = "rgba(226, 232, 240, 0.82)";
    ctx.textAlign = "center";
    ctx.textBaseline = "top";
    labels.forEach((label, idx) => {
        const x = chartLeft + stepX * idx;
        const text = hgEllipsize(ctx, label, Math.max(stepX - 12, 60));
  	    ctx.fillText(text, x, chartBottom + 10);
    });
    return true;
}

function hgRenderDatasetChart(canvas, chartType, rawEntries, indexAxis, paletteIndex) {
    const entries = rawEntries || [];
    if (!entries.length) return null;
    if (chartType === "line") {
        const labels = entries.map((entry) => hgFormatBucketLabel(entry.Bucket || entry.bucket));
        const values = entries.map((entry) => hgSafeValue(entry.Count ?? entry.count ?? 0));
        const color = hgGetPaletteColor(0, paletteIndex);
        const success = hgDrawLine(canvas, labels, values, color);
        return success ? { success: true, colors: values.map(() => color) } : null;
    }
    const labels = entries.map((entry, idx) => entry.Label || entry.label || entry.Code || entry.code || entry.Bucket || entry.bucket || `Item ${idx + 1}`);
    const values = entries.map((entry) => hgSafeValue(entry.Count ?? entry.count ?? 0));
    const colors = entries.map((entry, idx) => hgPickColor(entry, idx, paletteIndex));
    if (chartType === "doughnut") {
        const dataset = { values, colors, labels };
        const meta = hgDrawDoughnut(canvas, dataset, null);
        return meta ? { success: true, colors, meta: { type: "doughnut", dataset, activeIndex: null, ...meta } } : null;
    }
    const horizontal = indexAxis === "y";
    const success = horizontal ? hgDrawHorizontalBar(canvas, labels, values, colors) : hgDrawHorizontalBar(canvas, labels, values, colors);
    return success ? { success: true, colors } : null;
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
        const card = canvas.closest(".hg-chart-card");
        let measuring = false;
        if (card && !card.classList.contains("has-chart")) {
            card.classList.add("is-measuring");
            measuring = true;
        }
        const result = hgRenderDatasetChart(canvas, chartType, entries, indexAxis, index);
        if (card && measuring) {
            card.classList.remove("is-measuring");
        }
        if (result && result.success && card) {
            card.classList.add("has-chart");
            if (Array.isArray(result.colors)) {
                const fallbackItems = card.querySelectorAll(".hg-chart-fallback [data-hg-entry-index]");
                fallbackItems.forEach((item) => {
                    const idx = Number(item.dataset.hgEntryIndex);
                    if (!Number.isFinite(idx)) return;
                    const color = result.colors[idx];
                    if (color) {
                        item.style.setProperty("--hg-bar-color", color);
                        const fill = item.querySelector(".hg-chart-bar-fill");
                        if (fill) {
                            fill.style.background = color;
                        }
                    }
                });
            }
            if (result.meta && result.meta.type === "doughnut") {
                canvas.__hgMeta = result.meta;
                hgAttachDoughnutInteractions(canvas);
            } else {
                canvas.__hgMeta = null;
            }
        }
    });
}

function hgAttachDoughnutInteractions(canvas) {
    if (canvas.__hgHasHover) return;
    const rerender = (activeIdx) => {
        const meta = canvas.__hgMeta;
        if (!meta || !meta.dataset) {
            return null;
        }
        const next = hgDrawDoughnut(canvas, meta.dataset, Number.isFinite(activeIdx) ? activeIdx : null);
        if (!next) {
            return null;
        }
        const finalMeta = {
            ...meta,
            ...next,
            type: "doughnut",
            dataset: meta.dataset,
            activeIndex: Number.isFinite(activeIdx) ? activeIdx : null,
        };
        canvas.__hgMeta = finalMeta;
        return finalMeta;
    };
    const handleMove = (event) => {
        const meta = canvas.__hgMeta;
        if (!meta || !meta.segments || !meta.segments.length) {
            if (meta && meta.activeIndex !== null) {
                rerender(null);
            }
            hgHideTooltip();
            canvas.style.cursor = "default";
            return;
        }
        const rect = canvas.getBoundingClientRect();
        const x = event.clientX - rect.left;
        const y = event.clientY - rect.top;
        const dx = x - meta.cx;
        const dy = y - meta.cy;
        const distance = Math.sqrt(dx * dx + dy * dy);
        if (distance < meta.innerRadius * 0.92 || distance > meta.outerRadius + 2) {
            if (meta.activeIndex !== null) {
                rerender(null);
            }
            hgHideTooltip();
            canvas.style.cursor = "default";
            return;
        }
        let angle = Math.atan2(dy, dx);
        if (angle < 0) {
            angle += Math.PI * 2;
        }
        const segment = meta.segments.find((seg) => (seg.wrap ? angle >= seg.start || angle <= seg.end : angle >= seg.start && angle <= seg.end));
        if (!segment) {
            if (meta.activeIndex !== null) {
                rerender(null);
            }
            hgHideTooltip();
            canvas.style.cursor = "default";
            return;
        }
        canvas.style.cursor = "pointer";
        let segmentInfo = segment;
        if (meta.activeIndex !== segment.index) {
            const refreshed = rerender(segment.index);
            if (refreshed && Array.isArray(refreshed.segments)) {
                const match = refreshed.segments.find((seg) => seg.index === segment.index);
                if (match) {
                    segmentInfo = match;
                }
            }
        }
        const percent = Math.round(segmentInfo.percent * 1000) / 10;
        const valueText = segmentInfo.value.toLocaleString("es-MX");
        hgShowTooltip(event.clientX, event.clientY, `<strong>${segmentInfo.label || "Elemento"}</strong><span>${valueText} · ${percent}%</span>`);
    };
    canvas.addEventListener("mousemove", handleMove);
    canvas.addEventListener("mouseleave", () => {
        const meta = canvas.__hgMeta;
        if (meta && meta.activeIndex !== null) {
            rerender(null);
        }
        hgHideTooltip();
      	 canvas.style.cursor = "default";
    });
    canvas.__hgHasHover = true;
}

// Session expiration monitoring
const SESSION_WARNING_THRESHOLD_MS = 5 * 60 * 1000; // 5 minutes
let sessionCheckInterval = null;
let sessionWarningShown = false;

function hgInitSessionMonitor() {
    // Check session every 30 seconds
    sessionCheckInterval = setInterval(hgCheckSession, 30000);
    // Also check immediately
    hgCheckSession();
}

function hgCheckSession() {
    if (!window.sessionExpiresAt) {
        return;
    }

    const now = Date.now();
    const expiresAt = window.sessionExpiresAt;
    const timeRemaining = expiresAt - now;

    // If session already expired, redirect to login
    if (timeRemaining <= 0) {
        window.location.href = "/login";
        return;
    }

    // Show warning if within threshold and not already shown
    if (timeRemaining <= SESSION_WARNING_THRESHOLD_MS && !sessionWarningShown) {
        hgShowSessionWarning(timeRemaining);
    }
}

function hgShowSessionWarning(initialTimeRemaining) {
    sessionWarningShown = true;
    const modal = document.getElementById("session-warning-modal");
    const countdown = document.getElementById("session-countdown");
    const extendBtn = document.getElementById("extend-session-btn");
    const logoutBtn = document.getElementById("logout-now-btn");

    if (!modal || !countdown || !extendBtn || !logoutBtn) {
        return;
    }

    modal.style.display = "flex";

    // Update countdown every second
    const countdownInterval = setInterval(() => {
        const now = Date.now();
        const timeRemaining = window.sessionExpiresAt - now;

        if (timeRemaining <= 0) {
  	         clearInterval(countdownInterval);
  	         window.location.href = "/login";
  	         return;
        }

        const minutes = Math.floor(timeRemaining / 60000);
        const seconds = Math.floor((timeRemaining % 60000) / 1000);
        countdown.textContent = `${minutes}:${seconds.toString().padStart(2, "0")}`;
    }, 1000);

    // Handle extend session
    extendBtn.onclick = async () => {
        try {
            const response = await fetch("/session/refresh", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
            });

            if (response.ok) {
                const data = await response.json();
                if (data.success && data.expiresAt) {
                    // Update session expiration time
                    window.sessionExpiresAt = data.expiresAt * 1000;
                    sessionWarningShown = false;
                    clearInterval(countdownInterval);
                  	 modal.style.display = "none";

                    // Show success flash
            	       const flashContainer =
                        document.querySelector(".hg-flashes") ||
                        (() => {
                            const container = document.createElement("div");
                            container.className = "hg-flashes";
                            const main = document.querySelector(".hg-main");
                            if (main) {
                            	 main.insertBefore(container, main.firstChild);
                            }
                            return container;
                        })();

                    const flash = document.createElement("div");
                  	 flash.className = "hg-flash hg-flash-success";
                    flash.textContent = "Sesión extendida exitosamente";
                    flashContainer.appendChild(flash);

  	                 setTimeout(() => {
                        flash.classList.add("is-dismissed");
                        flash.addEventListener("transitionend", () => flash.remove(), { once: true });
                    }, 4000);
                }
            } else {
                throw new Error("Failed to refresh session");
            }
        } catch (error) {
            console.error("Error refreshing session:", error);
            alert("No se pudo extender la sesión. Por favor, inicia sesión nuevamente.");
    	     window.location.href = "/login";
        }
    };

    // Handle logout
    logoutBtn.onclick = () => {
        // Find logout form and submit it
        const logoutForm = document.querySelector('form[action="/logout"]');
      	 if (logoutForm) {
            logoutForm.submit();
        } else {
            window.location.href = "/login?logout=1";
        }
    };
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

    document.querySelectorAll("form.hg-autoform input").forEach((input) => {
    	 input.addEventListener("change", () => {
            const form = input.closest("form.hg-autoform");
            if (!form) {
    	       	 return;
    	       }
    	       form.submit();
    	 });
    });

    document.querySelectorAll("[data-hg-stream-selector]").forEach((select) => {
    	 select.addEventListener("change", () => {
            const form = select.closest("form");
            if (form) {
    	       	 form.submit();
    	       }
    	 });
    });

    hgInitDashboardCharts();

    if (window.sessionExpiresAt) {
  	   	 hgInitSessionMonitor();
    }
});

window.addEventListener(
    "scroll",
    () => {
        hgHideTooltip();
    },
    true
);