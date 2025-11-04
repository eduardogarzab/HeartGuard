const Xml = {
    parse(xmlString) {
        if (!xmlString || typeof xmlString !== "string") {
            throw new Error("Respuesta vacía");
        }
        const parser = new window.DOMParser();
        const doc = parser.parseFromString(xmlString, "application/xml");
        const parserError = doc.querySelector("parsererror");
        if (parserError) {
            throw new Error("No se pudo interpretar la respuesta XML");
        }
        if (doc.querySelector("response > error")) {
            const code = doc.querySelector("response > error > code")?.textContent || "error";
            const message = doc.querySelector("response > error > message")?.textContent || "Error en la solicitud";
            const err = new Error(message);
            err.code = code;
            throw err;
        }
        return doc;
    },

    text(root, selector, fallback = "") {
        if (!root) {
            return fallback;
        }
        const node = root.querySelector(selector);
        return node ? node.textContent.trim() : fallback;
    },

    integer(root, selector, fallback = 0) {
        if (!root) {
            return fallback;
        }
        const value = this.text(root, selector, "");
        const parsed = parseInt(value, 10);
        return Number.isNaN(parsed) ? fallback : parsed;
    },

    float(root, selector, fallback = 0) {
        if (!root) {
            return fallback;
        }
        const value = this.text(root, selector, "");
        const parsed = parseFloat(value);
        return Number.isNaN(parsed) ? fallback : parsed;
    },

    bool(root, selector, fallback = false) {
        if (!root) {
            return fallback;
        }
        const value = this.text(root, selector, "").toLowerCase();
        if (value === "true" || value === "1" || value === "yes") {
            return true;
        }
        if (value === "false" || value === "0" || value === "no") {
            return false;
        }
        return fallback;
    },

    mapNodes(root, selector, mapper) {
        if (!root) {
            return [];
        }
        return Array.from(root.querySelectorAll(selector)).map(mapper);
    }
};
