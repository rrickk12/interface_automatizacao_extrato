// static/js/debug.js

export function log(...args) {
  if (window.DEBUG_MODE) {
    console.log("[DEBUG]", ...args);
  }
}

export function warn(...args) {
  if (window.DEBUG_MODE) {
    console.warn("[DEBUG WARN]", ...args);
  }
}

export function error(...args) {
  if (window.DEBUG_MODE) {
    console.error("[DEBUG ERROR]", ...args);
  }
}
