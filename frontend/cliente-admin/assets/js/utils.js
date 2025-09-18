export const $ = (sel, parent = document) => parent.querySelector(sel);
export const $$ = (sel, parent = document) => Array.from(parent.querySelectorAll(sel));

export const el = (tag, props = {}) => Object.assign(document.createElement(tag), props);

export const fmt = {
	int: (n) => new Intl.NumberFormat("es-MX").format(n),
	time: (ts) => new Date(ts).toLocaleString("es-MX"),
	timeShort: (ts) => new Date(ts).toLocaleTimeString("es-MX", { hour: "2-digit", minute: "2-digit" }),
	date: (ts) => new Date(ts).toLocaleDateString("es-MX"),
};

// Debounce para optimizar eventos frecuentes
export const debounce = (func, wait) => {
	let timeout;
	return function executedFunction(...args) {
		const later = () => {
			clearTimeout(timeout);
			func(...args);
		};
		clearTimeout(timeout);
		timeout = setTimeout(later, wait);
	};
};

// Logger con niveles
export const logger = {
	debug: (...args) => CONFIG.DEMO_MODE && console.log("[DEBUG]", ...args),
	info: (...args) => console.info("[INFO]", ...args),
	warn: (...args) => console.warn("[WARN]", ...args),
	error: (...args) => console.error("[ERROR]", ...args),
};
